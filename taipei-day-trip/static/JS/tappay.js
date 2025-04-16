// tappay.js
export function setupTapPay(appId, appKey) {
    TPDirect.setupSDK(appId, appKey, "sandbox");
  
    TPDirect.card.setup({
      fields: {
        number: { element: "#card-number", placeholder: "**** **** **** ****" },
        expirationDate: { element: "#card-expiration-date", placeholder: "MM / YY" },
        ccv: { element: "#card-ccv", placeholder: "CVV" }
      },
      styles: { 'input': { 'color': 'gray' }, ':focus': {'color': 'Gold '},'.valid': { 'color': 'green' }, '.invalid': { 'color': 'red' } }
    });
  }
  
  export function bindPaymentButton(callback) {
    const payButton = document.querySelector(".submit-btn");
    payButton.addEventListener("click", () => {
      const status = TPDirect.card.getTappayFieldsStatus();
      if (!status.canGetPrime) {
        alert("請正確填寫卡片資訊！");
        return;
      }
  
      TPDirect.card.getPrime((result) => {
        if (result.status !== 0) {
          alert("取得 Prime 失敗");
          return;
        }
        callback(result.card.prime);
      });
    });
  }
  