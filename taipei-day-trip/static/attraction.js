document.addEventListener("DOMContentLoaded", async function() {
    // 修正錯誤的 URL 參數解析
    const pathParts = window.location.pathname.split("/");
const attractionId = pathParts[pathParts.length - 1];
    
    if (!attractionId) {
        console.error("無效的景點 ID");
        return;
    }

    const apiUrl = `http://127.0.0.1:8000/api/attractions/${attractionId}`;
    //http://13.239.58.95:8000/
    //http://127.0.0.1:8000/
    console.log("API URL:", apiUrl);  // 確認 API URL 是否正確

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            throw new Error(`HTTP 錯誤！狀態碼: ${response.status}`);
        }
        const data = await response.json();
        console.log("API 回傳的資料:", data);  // 確認 API 回傳的內容

        // 修正資料存取方式
        renderAttraction(data.data);
    } catch (error) {
        console.error("Error loading attraction data:", error);
    }
});

function renderAttraction(attraction) {
    document.getElementById("attraction-name").textContent = attraction.name;
    document.getElementById("attraction-category-mrt").textContent = attraction.category+" at "+attraction.mrt;
    document.getElementById("description").textContent = attraction.description;
    document.getElementById("address").textContent = attraction.address;
    document.getElementById("transportation").textContent = attraction.transport;

    let currentImageIndex = 0;
    const images = attraction.images;
    const mainImage = document.getElementById("main-image");

    if (images.length > 0) {
        mainImage.src = images[currentImageIndex];
    }

    const indicatorsContainer = document.querySelector(".indicators");
    while (indicatorsContainer.firstChild) {
        indicatorsContainer.removeChild(indicatorsContainer.firstChild);
    }

    //動態建立圓點
    images.forEach((_, index) => {
        const dot = document.createElement("span");
        dot.classList.add("dot");
        if (index === currentImageIndex) {
            dot.classList.add("active");
        }
        dot.addEventListener("click", () => {
            currentImageIndex = index;
            updateSlideshow();
        });
        indicatorsContainer.appendChild(dot);
    });

    document.getElementById("prev-btn").addEventListener("click", function() {
        currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
        mainImage.src = images[currentImageIndex];
        updateSlideshow();
    });

    document.getElementById("next-btn").addEventListener("click", function() {
        currentImageIndex = (currentImageIndex + 1) % images.length;
        mainImage.src = images[currentImageIndex];
        updateSlideshow();
    });

    function updateSlideshow() {
        mainImage.src = images[currentImageIndex];

        // 更新圓點的 active 狀態
        const dots = document.querySelectorAll(".dot");
        dots.forEach((dot, index) => {
            dot.classList.toggle("active", index === currentImageIndex);
        });
    }

    updateSlideshow();

    const priceElement = document.getElementById("price");
    const morningRadio = document.getElementById("morning");
    const afternoonRadio = document.getElementById("afternoon");

    function updatePrice(price) {
        priceElement.textContent = price;
    }

    morningRadio.addEventListener("change", () => updatePrice(2000));
    afternoonRadio.addEventListener("change", () => updatePrice(2500));

    morningRadio.checked = true;
    updatePrice(2000);
}
