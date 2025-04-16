import { setupTapPay, bindPaymentButton } from "./tappay.js";

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

let currentBooking = null; // 全域變數，儲存 /api/booking 拿到的資料

document.addEventListener("DOMContentLoaded", async () => {
  setupTapPay(159815, "app_2SUKCo0UuUWUPSFJbBqKadBYBwMcaNKASef9BTEZh2aEL5uXDa7j5L30heEA");

  // 抓 booking 資料（假設你之前也這樣做）
  const token = localStorage.getItem("token");
  if (token) {
    try {
      const res = await fetch("/api/booking", {
        method: "GET",
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.data) {
        currentBooking = data.data;
      }
    } catch (err) {
      console.error("取得 booking 資料錯誤：", err);
    }
  }

  // 綁定付款按鈕
  bindPaymentButton(async (prime) => {
    if (!token) {
      alert("請先登入");
      return;
    }

    const name = document.getElementById("contact-name").value.trim();
    const email = document.getElementById("contact-email").value.trim();
    const phone = document.getElementById("contact-phone").value.trim();

    // 檢查 contact 資料
    if (!name || !email || !phone) {
      alert("請填寫聯絡人資訊！");
      return;
    }

    // 檢查 booking 是否有抓到
    if (!currentBooking) {
      alert("無法取得預訂資料，請重新整理頁面");
      return;
    }

    const body = {
      prime: prime,
      order: {
        price: currentBooking.price,
        trip: {
          attraction: {
            id: currentBooking.attraction.id,
            name: currentBooking.attraction.name,
            address: currentBooking.attraction.address,
            image: currentBooking.attraction.image
          },
          date: currentBooking.date,
          time: currentBooking.time
        },
        contact: {
          name: name,
          email: email,
          phone: phone
        }
      }
    };

    console.log("送出訂單：", body); // ✅ DEBUG 用

    try {
      const res = await fetch("/api/orders", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(body)
      });

      const result = await res.json();

      if (result.data && result.data.number) {
        window.location.href = `/thankyou?number=${result.data.number}`;
      } else {
        alert(result.message || "付款失敗，請稍後再試");
      }
    } catch (error) {
      console.error("付款錯誤：", error);
      alert("伺服器錯誤");
    }
  });
});