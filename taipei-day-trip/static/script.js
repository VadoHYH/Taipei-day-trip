// 確保 DOM 加載完畢
document.addEventListener("DOMContentLoaded", () => {
    fetchMRTStations();
    fetchAttractions(); // 初始載入
});

// 變數設定
let currentPage = 1;    // 初始載入 page=1（因為 page=0 已經加載）
let isLoading = false;
let currentKeyword = ""; // 存儲當前搜尋的關鍵字

// 取得 MRT 站名並插入頁面
function fetchMRTStations() {
    fetch("/api/mrts")
    .then(response => response.json())
    .then(data => {
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

// 建立單一景點卡片
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

// **載入景點資料**
function fetchAttractions(keyword = "", page = 0, isNewSearch = false) {
    let url = `/api/attractions?page=${page}`;
    if (keyword) {
        url += `&keyword=${encodeURIComponent(keyword)}`;
    }

    fetch(url)
    .then(response => response.json())
    .then(data => {
        if (!data || !data.data || !Array.isArray(data.data)) {
            throw new Error("API 回應格式錯誤");
        }

        const spotsContainer = document.getElementById("spots");

        if (isNewSearch) {
            spotsContainer.innerHTML = ""; // 只有搜尋時才清空資料
        }

        data.data.forEach(attraction => {
            let card = createSpotCard(attraction);
            spotsContainer.appendChild(card);
        });

        // 更新 `currentPage` 為 `nextPage`
        currentPage = data.nextPage !== null ? data.nextPage : null;
        isLoading = false;
    })
    .catch(error => console.error("無法載入景點:", error));
}

// **搜尋功能（依關鍵字篩選景點）**
document.querySelector(".search-btn").addEventListener("click", () => {
    const keyword = document.querySelector(".search-box input").value.trim();

    if (keyword !== currentKeyword) {
        currentKeyword = keyword;
        currentPage = 0; // 搜尋時重新開始載入
        isLoading = false;
        fetchAttractions(keyword, 0, true);
    }
});

// **MRT 站篩選景點**
function searchByMRT(mrtName) {
    const searchInput = document.querySelector(".search-box input");
    searchInput.value = mrtName;
    document.querySelector(".search-btn").click();  // 直接觸發搜尋
}

// **滾動事件監聽**
window.addEventListener("scroll", () => {
    if (isLoading || currentPage === null) return;  

    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = window.innerHeight;

    if (scrollTop + clientHeight >= scrollHeight - 100) {
        loadMoreAttractions();
    }
});

// **載入更多景點**
function loadMoreAttractions() {
    if (isLoading || currentPage === null) return;
    isLoading = true;

    let keyword = currentKeyword || document.querySelector(".search-box input").value.trim();
    fetchAttractions(keyword, currentPage, false);
}
