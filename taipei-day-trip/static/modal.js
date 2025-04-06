// 共用的錯誤訊息取得函式
function getErrorMessage(data, fallbackMsg = "發生未知錯誤") {
    return data.message || data.detail || fallbackMsg;
}

// 檢查登入狀態
document.addEventListener("DOMContentLoaded", async () => {
    try {
        const token = localStorage.getItem("token");
        if (!token) {
            setupLoginModalLoader();
            return;
        }

        const authRes = await fetch("/api/user/auth", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const authData = await authRes.json();

        if (authRes.ok && authData.data) {
            updateHeaderToLogout();
        } else {
            localStorage.removeItem("token");
            setupLoginModalLoader();
        }
    } catch (error) {
        console.error("無法確認登入狀態：", error);
    }
});

// 處理「登入/註冊」按鈕點擊 → 載入彈窗 HTML
async function setupLoginModalLoader() {
    try {
        const response = await fetch("/static/login-modal.html");
        const modalHTML = await response.text();

        const parser = new DOMParser();
        const doc = parser.parseFromString(modalHTML, "text/html");
        const modalTemplate = doc.getElementById("login-modal-template");

        if (!modalTemplate) throw new Error("無法取得 login modal template");

        const loginTrigger = document.getElementById("login-trigger");
        loginTrigger.addEventListener("click", (e) => {
            e.preventDefault();
            const modalInstance = modalTemplate.content.cloneNode(true);
            document.body.appendChild(modalInstance);
            setupLoginModal(); // 初始化彈窗功能
        });
    } catch (error) {
        console.error("載入登入視窗失敗：", error);
    }
}

// 初始化登入彈窗功能
function setupLoginModal() {
    const loginModal = document.getElementById("login-modal");

    loginModal.style.display = "flex";
    loginModal.classList.add("show");

    const closeBtn = loginModal.querySelector(".close-btn");
    const loginForm = loginModal.querySelector("#login-form");
    const signupForm = loginModal.querySelector("#signup-form");
    const modalTitle = loginModal.querySelector("#modal-title");

    // 切換至註冊表單
    loginModal.querySelector("#show-signup").addEventListener("click", () => {
        loginForm.style.display = "none";
        signupForm.style.display = "block";
        modalTitle.innerText = "註冊會員帳號";
    });

    // 切換至登入表單
    loginModal.querySelector("#show-login").addEventListener("click", () => {
        loginForm.style.display = "block";
        signupForm.style.display = "none";
        modalTitle.innerText = "登入會員帳號";
    });

    // 關閉彈窗按鈕
    closeBtn.addEventListener("click", () => {
        loginModal.remove();
    });

    // 按下 Esc 關閉彈窗
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && loginModal) loginModal.remove();
    });

    // 處理登入送出
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const email = loginModal.querySelector("#login-email").value.trim();
        const password = loginModal.querySelector("#login-password").value.trim();
        const errorEl = loginModal.querySelector("#login-error");
        errorEl.textContent = "";

        if (!email || !password) {
            errorEl.textContent = "請輸入帳號與密碼";
            return;
        }

        try {
            const res = await fetch("/api/user/auth", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const data = await res.json();

            if (res.ok && data.data && data.data.token) {
                localStorage.setItem("token", data.data.token); // 儲存 Token
                loginModal.remove();
                updateHeaderToLogout();
            } else {
                errorEl.textContent = getErrorMessage(data, "登入失敗");
            }

        } catch (err) {
            errorEl.textContent = "無法連線伺服器，請稍後再試";
        }
    });


    // 處理註冊送出
    signupForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const name = loginModal.querySelector("#signup-name").value.trim();
        const email = loginModal.querySelector("#signup-email").value.trim();
        const password = loginModal.querySelector("#signup-password").value.trim();
        const errorEl = loginModal.querySelector("#signup-error");
        errorEl.textContent = "";

        if (!name || !email || !password) {
            errorEl.textContent = "請輸入完整註冊資訊";
            return;
        }

        try {
            const res = await fetch("/api/user", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password }),
            });

            const data = await res.json();

            if (res.ok && data.ok) {
                // 註冊成功 → 切換回登入
                signupForm.style.display = "none";
                loginForm.style.display = "block";
                modalTitle.innerText = "登入會員帳號";
                loginModal.querySelector("#login-error").textContent = "註冊成功，請登入！";
            } else {
                errorEl.textContent = getErrorMessage(data, "註冊失敗，請確認填寫資訊");
            }
        } catch (err) {
            errorEl.textContent = "無法連線伺服器，請稍後再試";
        }
    });
}

// 更新 Header 為「登出系統」
function updateHeaderToLogout() {
    const headerBtn = document.getElementById("login-trigger");
    if (!headerBtn) return;

    const newBtn = document.createElement("a");
    newBtn.innerText = "登出系統";
    newBtn.id = "logout-trigger";
    newBtn.href = "#";

    headerBtn.replaceWith(newBtn);

    newBtn.addEventListener("click", (e) => {
        e.preventDefault();
        logoutUser();
    });
}

// 登出功能（直接清除 token 並更新 Header）
function logoutUser() {
    localStorage.removeItem("token");
    updateHeaderToLogin(); // 改回「登入/註冊」按鈕
}

// 更新 Header 為「登入/註冊」
function updateHeaderToLogin() {
    const headerBtn = document.getElementById("logout-trigger");
    if (!headerBtn) return;

    const newBtn = document.createElement("a");
    newBtn.innerText = "登入/註冊";
    newBtn.id = "login-trigger";
    newBtn.href = "#";

    headerBtn.replaceWith(newBtn);

    setupLoginModalLoader(); // 重新綁定登入按鈕
}

// 登入成功後更新 header
async function handleLoginSuccess(token) {
    if (!token) {
        console.error("登入成功但未獲得 token");
        return;
    }
    localStorage.setItem("token", token);
    console.log("Token 儲存成功:", token);
    location.reload(); // 重新整理頁面以更新狀態
}