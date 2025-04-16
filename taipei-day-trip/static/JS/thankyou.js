// thankyou.js
document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const orderNumber = params.get("number");
  
    if (orderNumber) {
      document.getElementById("order-num").textContent = orderNumber;
    } else {
      document.getElementById("order-num").textContent = "查無訂單編號";
    }
  });
  