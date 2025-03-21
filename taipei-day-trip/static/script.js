// 確保 DOM 加載完畢
document.addEventListener("DOMContentLoaded", () => {
    fetchMRTStations();
    fetchAttractions();
});

// 取得 MRT 站名並插入頁面
function fetchMRTStations() {
    fetch("/api/mrts")
    .then(response => response.json())
    .then(data => {
        console.log("MRT API 回應:", data);
        if (!data || !data.data) throw new Error("API 回應格式錯誤");

        const mrtScroll = document.querySelector(".mrt-scroll");
        mrtScroll.innerHTML = ""; // 清空舊資料

        data.data.forEach(station => {
            let span = document.createElement("span");
            span.textContent = station;
            span.addEventListener("click", () => searchByMRT(station));
            mrtScroll.appendChild(span);
        });
    })
    .catch(error => console.error("無法載入 MRT 站名:", error));
}

// 建立單一景點卡片 (取代 innerHTML)
function createSpotCard(attraction) {
    let card = document.createElement("div");
    card.classList.add("spot-card");

    // 圖片區塊
    let imageContainer = document.createElement("div");
    imageContainer.classList.add("spot-image");

    let img = document.createElement("img");
    img.src = attraction.images?.[0] || "default.jpg";
    img.alt = attraction.name;

    let nameOverlay = document.createElement("div");
    nameOverlay.classList.add("spot-name-overlay");
    nameOverlay.textContent = attraction.name;

    imageContainer.appendChild(img);
    imageContainer.appendChild(nameOverlay);

    // 景點資訊
    let info = document.createElement("div");
    info.classList.add("spot-info");

    let mrt = document.createElement("span");
    mrt.classList.add("spot-mrt");
    mrt.textContent = attraction.mrt || "無";

    let category = document.createElement("span");
    category.classList.add("spot-category");
    category.textContent = attraction.category;

    info.appendChild(mrt);
    info.appendChild(category);

    // 組合所有元素
    card.appendChild(imageContainer);
    card.appendChild(info);

    return card;
}

// 使用 createSpotCard 來載入景點
function fetchAttractions(keyword = "") {
    let url = "/api/attractions";
    if (keyword) {
        url += `?keyword=${encodeURIComponent(keyword)}`;
    }

    fetch(url)
    .then(response => response.json())
    .then(data => {
        console.log("景點 API 回應:", data);
        if (!data || !data.data || !Array.isArray(data.data)) {
            throw new Error("API 回應格式錯誤");
        }

        const spotsContainer = document.getElementById("spots");
        spotsContainer.innerHTML = ""; // 清空舊資料

        data.data.forEach(attraction => {
            let card = createSpotCard(attraction);
            spotsContainer.appendChild(card);
        });
    })
    .catch(error => console.error("無法載入景點:", error));
}

// 搜尋功能（依關鍵字篩選景點）
document.querySelector(".search-btn").addEventListener("click", () => {
    const keyword = document.querySelector(".search-box input").value;
    fetchAttractions(keyword);
});

// MRT 站篩選景點
function searchByMRT(mrtName) {
    const searchInput = document.querySelector(".search-box input");
    searchInput.value = mrtName; // 設定搜尋框的值
    fetchAttractions(mrtName); // 執行景點搜尋
}

// MRT 滾動按鈕事件
document.addEventListener("DOMContentLoaded", () => {
    const mrtScroll = document.querySelector(".mrt-scroll");
    const buttons = document.querySelectorAll(".mrt-filter button");

    const scrollAmount = 200; // 每次滾動 200px

    buttons[0].addEventListener("click", () => {
        mrtScroll.scrollBy({ left: -scrollAmount, behavior: "smooth" });
    });

    buttons[1].addEventListener("click", () => {
        mrtScroll.scrollBy({ left: scrollAmount, behavior: "smooth" });
    });
});

// 無限滾動 
let currentPage = 1;
let isLoading = false;

window.addEventListener("scroll", () => {
    if (isLoading || currentPage === null) return;  

    const scrollPosition = window.innerHeight + window.scrollY;
    const documentHeight = document.documentElement.offsetHeight;

    if (scrollPosition >= documentHeight - 100) { 
        loadMoreAttractions();  // 自動載入時確保關鍵字不丟失
    }
});

function loadMoreAttractions() {
    if (isLoading || currentPage === null) return;  

    isLoading = true; 

    // 確保帶入關鍵字
    const keyword = document.querySelector(".search-box input").value.trim();
    let url = `/api/attractions?page=${currentPage}`;
    if (keyword) {
        url += `&keyword=${encodeURIComponent(keyword)}`;  // 🔹 加入 keyword 參數
    }

    fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log("載入更多景點 API 回應:", data);

            if (!data || !data.data || !Array.isArray(data.data)) {
                throw new Error("API 回應格式錯誤");
            }

            const spotsContainer = document.getElementById("spots");

            data.data.forEach(attraction => {
                let card = document.createElement("div");
                card.classList.add("spot-card");
                card.innerHTML = `
                    <div class="spot-image">
                        <img src="${attraction.images?.[0] || 'default.jpg'}" alt="${attraction.name}">
                        <div class="spot-name-overlay">${attraction.name}</div>
                    </div>
                    <div class="spot-info">
                        <span class="spot-mrt">${attraction.mrt || "無"}</span>
                        <span class="spot-category">${attraction.category}</span>
                    </div>
                `;
                spotsContainer.appendChild(card);
            });

            // 🔹 檢查是否還有下一頁
            if (data.nextPage !== null) {
                currentPage = data.nextPage;
                isLoading = false;
            } else {
                currentPage = null;
                console.log("沒有更多資料了");
            }
        })
        .catch(error => {
            console.error("無法載入更多景點:", error);
            isLoading = false;
        });
}
