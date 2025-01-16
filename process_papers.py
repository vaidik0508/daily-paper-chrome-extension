import os
from pydantic import BaseModel
from typing import Dict, Any, List
# from langchain_ollama.llms import OllamaLLM
import fitz, json, shutil
from crewai.tools import BaseTool
from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import arxiv
import requests
import asyncio
from langchain_openai import ChatOpenAI
from crewai import LLM
load_dotenv(override=True)

MAX_PAPERS = int(os.getenv('MAX_PAPERS', 3))
MAX_RETRIES = 3
MAX_WORKERS = 4

model = os.getenv('model')
endpoint = os.getenv('lmstudio_endpoint')
api_key = os.getenv('api_key')

llm = LLM(model=model, temperature=0.25, base_url= endpoint, api_key=api_key)
# llm = ChatOpenAI(model=model, temperature=0.25, base_url= endpoint, api_key=api_key)

class PaperAnalysis(BaseModel):
    title: str
    authors: List[str]
    past_work: str
    problems: str
    solutions: str
    entire_process_of_work: str
    key_technologies: List[str]
    new_or_SOTA_contributions: str
    LeTAX_code: str
    summary: str

async def save_analysis_in_mongo(collection: str, paper: Dict[str, Any]) -> bool:
    retries = 0
    while retries < MAX_RETRIES:
        try:
            mongodb_client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
            mongodb = mongodb_client[os.getenv("MONGODB_DB_NAME")]
            collection = mongodb[collection]
            await collection.insert_one(paper)
            mongodb_client.close()
            return True
        except Exception as e:
            print(f"Error saving to MongoDB (attempt {retries + 1}/{MAX_RETRIES}): {e}")
            retries += 1
            await asyncio.sleep(1)
    return False

def extract_text(pdf_path: str) -> str:
    try:
        document = fitz.open(pdf_path)
        text = ""
        for page in document:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

class ReadPDF(BaseTool):
    name: str = "ReadPDF"
    description: str = 'Read PDF and return text of it.'

    def _run(self, path: str) -> str:
        return extract_text(path)

def get_crew() -> Crew:
    research_paper_analyzer = Agent(
        role='Research Paper Analyzer',
        goal='Extract and summarize key information from research papers.',
        backstory="Expert in reading and understanding research papers.",
        tools=[ReadPDF()],
        llm=llm,
    )

    extract_and_summarize_task = Task(
        description=(
            "pdf path: {path}\n"
            "Read and analyze the research paper to extract: "
            "title, authors, past work, problems, solutions, "
            "key technologies, new contributions, process details, "
            "technical solution code, and summary."
        ),
        expected_output='JSON with keys: "title", "authors", "past_work", "problems", "solutions", "entire_process_of_work", "key_technologies", "new_or_SOTA_contributions", "LeTAX_code", "summary".',
        output_pydantic=PaperAnalysis,
        agent=research_paper_analyzer
    )

    return Crew(
        agents=[research_paper_analyzer],
        tasks=[extract_and_summarize_task],
        process=Process.sequential,
        output_token_usage=True,
        verbose=False
    )

async def analyze_paper(path: str) -> tuple[Dict[str, Any], Dict[str, int]]:
    research_crew = get_crew()
    result = await research_crew.kickoff_async(inputs={'path': path})
    result = result.tasks_output[-1].pydantic.model_dump()
    token = 0 #result['usage_metrics']
    result['usage_token'] = token
    return result, token

async def download_paper(output_folder: str, result: arxiv.Result) -> str:
    filename = f"{result.get_short_id().split('/')[-1]}.pdf"
    filepath = os.path.join(output_folder, filename)
    
    for attempt in range(MAX_RETRIES):
        try:
            async with asyncio.timeout(30):  # 30 seconds timeout
                response = requests.get(result.pdf_url)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"Downloaded: {result.title}")
                    return filepath
                else:
                    print(f"Failed to download: {result.title} (attempt {attempt + 1}/{MAX_RETRIES})")
        except Exception as e:
            print(f"Error downloading paper (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            await asyncio.sleep(1)
    return ""

async def fetch_papers(days: int = 1) -> List[str]:
    end_date = datetime.now(ZoneInfo("UTC"))
    start_date = end_date - timedelta(days=days)
    
    search = arxiv.Search(
        query="cat:cs.AI OR cat:cs.CV OR cat:cs.LG OR cat:cs.MA",
        max_results=MAX_PAPERS,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )

    output_folder = str(end_date.date())
    os.makedirs(output_folder, exist_ok=True)

    download_tasks = []
    for result in search.results():
        if len(download_tasks) >= MAX_PAPERS:
            break
            
        if start_date <= result.published <= end_date:
            download_tasks.append(download_paper(output_folder, result))

    downloaded_paths = await asyncio.gather(*download_tasks)
    return [path for path in downloaded_paths if path]

async def check_collection_exists(collection_name: str) -> bool:
    retries = 0
    while retries < MAX_RETRIES:
        try:
            mongodb_client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
            mongodb = mongodb_client[os.getenv("MONGODB_DB_NAME")]
            collection_names = await mongodb.list_collection_names()
            mongodb_client.close()
            return collection_name in collection_names
        except Exception as e:
            print(f"Error checking collection (attempt {retries + 1}/{MAX_RETRIES}): {e}")
            retries += 1
            await asyncio.sleep(1)
    return False

async def process_paper(folder_name: str, path: str) -> None:
    try:
        full_path = os.path.join(folder_name, path)
        result, _ = await analyze_paper(full_path)
        result['paper_id'] = path
        result['day'] = folder_name
        await save_analysis_in_mongo(folder_name, result)
        print(f"Processed paper: {path}")
    except Exception as e:
        print(f"Error processing paper {path}: {e}")

async def get_sync(last_n_days: int = 1) -> str:
    current_folder_name = str(datetime.now().date())
    
    if await check_collection_exists(current_folder_name):
        return 'Already processed today\'s papers'

    try:
        paper_paths = await fetch_papers(last_n_days)
        if not paper_paths:
            return 'No papers downloaded'
            
        print('Papers fetched successfully')
        folder_name = os.path.dirname(paper_paths[0])

        # Process papers in parallel using ThreadPoolExecutor
        tasks = []
        for path in paper_paths:
            tasks.append(process_paper(folder_name, os.path.basename(path)))
        
        await asyncio.gather(*tasks)
        return 'Processing completed successfully'

    except Exception as e:
        print(f"Error in sync process: {e}")
        return 'Error during processing'
        
    finally:
        if 'folder_name' in locals():
            shutil.rmtree(folder_name)

if __name__ == '__main__':
    asyncio.run(get_sync(last_n_days=1))
