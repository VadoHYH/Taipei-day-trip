document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("token");
  
    // 尚未登入則載入 modal
    if (!token) {
      await setupLoginModalLoader();
    }
  
    // 預定行程按鈕
    const bookingLink = document.getElementById("booking-trigger");
    if (bookingLink) {
      bookingLink.addEventListener("click", (event) => {
        if (!token) {
          event.preventDefault(); // 阻止跳轉
          const modalTrigger = document.getElementById("login-trigger");
          if (modalTrigger) modalTrigger.click();
        }
      });
    }
  
    // 以下是只有在 booking.html 頁面才會執行的邏輯
    const userNameElement = document.querySelector(".user-name");
    const contactNameInput = document.getElementById("contact-name");
    const contactEmailInput = document.getElementById("contact-email");
    const tourSection = document.getElementById("tourContainer");
    const noToursMessage = document.getElementById("noToursMessage");
    const tourTitle = document.querySelector(".tour-title");
    const tourImage = document.querySelector(".tour-image");
    const tourDate = document.getElementById("tour-date");
    const tourTime = document.getElementById("tour-time");
    const tourPrice = document.getElementById("tour-price");
    const totalPrice = document.getElementById("total-price");
    const tourAddress = document.getElementById("address");
    const contentSection = document.getElementById("contactSection");
    const paymentSection = document.getElementById("paymentSection");
    const paymentActions = document.getElementById("paymentActions");
  
    if (userNameElement && tourSection) {
      if (!token) {
        window.location.href = "/";
        return;
      }
  
      await fetchUserInfo(token, userNameElement);
  
      try {
        const res = await fetch("/api/booking", {
          method: "GET",
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });
  
        const data = await res.json();
  
        if (data.data) {
          const booking = data.data;
  
          // 顯示預定資訊
          tourTitle.textContent = `台北一日遊：${booking.attraction.name}`;
          tourImage.src = booking.attraction.image;
          tourDate.textContent = booking.date;
          tourTime.textContent = booking.time === "morning" ? "早上 9 點到下午 4 點" : "下午 2 點到晚上 9 點";
          tourPrice.textContent = booking.price;
          totalPrice.textContent = booking.price;
          tourAddress.textContent = booking.attraction.address;
        } else {
          tourSection.style.display = "none";
          contentSection.style.display = "none";
          paymentSection.style.display = "none";
          paymentActions.style.display = "none";
          noToursMessage.style.display = "block";
        }
      } catch (error) {
        console.error("載入 booking 錯誤：", error);
        tourSection.style.display = "none";
        contentSection.style.display = "none";
        paymentSection.style.display = "none";
        paymentActions.style.display = "none";
        noToursMessage.style.display = "block";
      }
  
      const deleteButton = document.querySelector(".delete-btn");
      if (deleteButton) {
        deleteButton.addEventListener("click", deleteTour);
      }


    }
  });
  
  async function fetchUserInfo(token, userNameElement) {
    try {
      const res = await fetch("/api/user/auth", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
  
      const result = await res.json();
      if (result.data && result.data.name) {
        const name = result.data.name;
        const email = result.data.email || "";
  
        // 原本的功能
        userNameElement.textContent = name;
  
        // 自動填入聯絡姓名與信箱
        const contactNameInput = document.getElementById("contact-name");
        const contactEmailInput = document.getElementById("contact-email");
        if (contactNameInput) contactNameInput.value = name;
        if (contactEmailInput) contactEmailInput.value = email;
      } else {
        userNameElement.textContent = "使用者";
      }
    } catch (err) {
      console.error("取得使用者資訊錯誤：", err);
      userNameElement.textContent = "使用者";
    }
  }
  
  // 刪除預訂行程
  function deleteTour() {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("請先登入");
      return;
    }
  
    fetch("/api/booking", {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    })
      .then(res => res.json())
      .then(data => {
        if (data.ok) {
          location.reload(); // 成功就重整頁面
        } else {
          alert(data.message || "刪除失敗");
        }
      })
      .catch(error => {
        console.error("刪除 booking 錯誤：", error);
        alert("伺服器錯誤");
      });
  }

// 登出按鈕功能
const logoutButton = document.getElementById("logout-btn"); // 這是你的登出按鈕 ID
if (logoutButton) {
  logoutButton.addEventListener("click", () => {
    localStorage.removeItem("token"); // 清除 token
    window.location.href = "/"; // 導回首頁
  });
}