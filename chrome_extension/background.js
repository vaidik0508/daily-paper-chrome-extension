chrome.runtime.onInstalled.addListener(() => {
    console.log('Extension installed');
  });
  
  // Function to communicate with the Python backend
  async function callPythonBackend() {
    try {
      const response = await fetch('http://localhost:5000/api', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: 'Hello from Chrome Extension' })
      });
      const data = await response.json();
      console.log('Response from Python backend:', data);
    } catch (error) {
      console.error('Error communicating with Python backend:', error);
    }
  }
  
  // Example usage
  callPythonBackend();
  