function showTab(tabName) {
    const tabs = ['analysis', 'newProduct', 'dermatologists'];
    tabs.forEach(tab => {
        document.getElementById(`${tab}Tab`).classList.add('hidden');
    });
    document.getElementById(`${tabName}Tab`).classList.remove('hidden');
}

async function analyzeImage() {
    const fileInput = document.getElementById('imageUpload');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select an image to analyze.');
        return;
    }
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post('/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    displayAnalysisResults(response.data);
}

function displayAnalysisResults(data) {
    const resultsDiv = document.getElementById('analysisResults');
    resultsDiv.innerHTML = `
        <h3>Detected Acne Types:</h3>
        <ul>${data.acne_types.map(type => `<li>${type}</li>`).join('')}</ul>
        <h3>Recommendations:</h3>
        <p>${data.recommendations}</p>
    `;
}

// Webcam functionality
let stream;
const video = document.getElementById('webcam');

async function startWebcam() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
    } catch (err) {
        console.error("Error accessing the webcam:", err);
        alert("Error accessing the webcam. Please make sure you have given permission and that no other application is using it.");
    }
}

startWebcam();

async function captureImage() {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const imageData = canvas.toDataURL('image/jpeg');
    
    const formData = new FormData();
    formData.append('image_data', imageData);

    const response = await axios.post('/analyze_webcam', formData);
    displayAnalysisResults(response.data);
}

async function newProductChallenge() {
    const productName = document.getElementById('productName').value;
    const ingredients = document.getElementById('ingredients').value;
    if (!productName || !ingredients) {
        alert('Please enter both product name and ingredients.');
        return;
    }

    const formData = new FormData();
    formData.append('product_name', productName);
    formData.append('ingredients', ingredients);

    const response = await axios.post('/new_product_challenge', formData);
    const resultsDiv = document.getElementById('challengeResults');
    resultsDiv.innerHTML = `<p>${response.data.result}</p>`;
}

async function searchDermatologists() {
    const lat = document.getElementById('latitude').value;
    const lon = document.getElementById('longitude').value;
    if (!lat || !lon) {
        alert('Please enter both latitude and longitude.');
        return;
    }
    const response = await axios.post('/search_dermatologists', `lat=${lat}&lon=${lon}`, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    if (response.data.success) {
        const tableBody = document.querySelector('#dermatologistsTable tbody');
        tableBody.innerHTML = response.data.dermatologists.map(derm => `
            <tr>
                <td class="border p-2">${derm.name}</td>
                <td class="border p-2">${derm.rating}</td>
                <td class="border p-2">${derm.distance} m</td>
            </tr>
        `).join('');
    } else {
        alert('Error searching for dermatologists.');
    }
}
