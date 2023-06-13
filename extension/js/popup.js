console.log('popup.js is loaded.');

document.addEventListener('DOMContentLoaded', async () => {
  const urlInput = document.getElementById('urlInput');
  const slider = document.getElementById('switchId');

  const { useCustomServer, baseServerURL } = await chrome.storage.local.get(['useCustomServer', 'baseServerURL']);
  if (!useCustomServer) {
    urlInput.style.display = 'none';
  }

  slider.checked = useCustomServer;
  urlInput.value = baseServerURL;

  urlInput.addEventListener('keypress', (e) => {
    if (e.key !== 'Enter') return;

    // validate that the entry is a valid http/https url
    if (!isValidUrl(e.target.value)) {
      e.target.style.border = '2px solid';
      e.target.style.borderColor = 'red';

      removeOutline(e.target);
      return;
    }

    // store it inside chrome storage
    e.target.style.border = '2px solid';
    e.target.style.borderColor = 'green';
    chrome.storage.local.set({ baseServerURL: e.target.value }).then(() => console.log('updated the baseServerURL!'));
    removeOutline(e.target);
  });

  slider.addEventListener('change', (e) => {
    if (e.target.checked) {
      urlInput.style.display = 'block';
    } else {
      urlInput.style.display = 'none';
      chrome.storage.local.set({ baseServerURL: 'https://decodify.hop.sh/transactions' }).then(() => console.log('updated the baseServerURL!'));
    }

    chrome.storage.local.set({ useCustomServer: e.target.checked }).then(() => console.log('updated the useCustomServer!'));
  });

  const isValidUrl = (inputURL) => {
    try {
      const url = new URL(inputURL);
      return url.pathname == '/transactions' ? true : false;
    } catch (error) {
      return false;
    }
  };

  const removeOutline = (el) => {
    setTimeout(() => {
      el.style.border = '1px solid';
      el.style.borderColor = 'black';
    }, 900);
  };
});
