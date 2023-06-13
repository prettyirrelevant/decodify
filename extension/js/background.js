console.log('background.js loaded.');

const getDefaultSettings = () => {
  return {
    useCustomServer: false,
    baseServerURL: 'https://decodify.hop.sh/transactions',
  };
};

const initializeExtension = () => {
  chrome.storage.local.get(['useCustomServer', 'baseServerURL']).then(({ useCustomServer, baseServerURL }) => {
    const defaultSettings = getDefaultSettings();

    defaultSettings.baseServerURL = baseServerURL || defaultSettings.baseServerURL;
    defaultSettings.useCustomServer = useCustomServer || defaultSettings.useCustomServer;

    chrome.storage.local.set(defaultSettings).then(() => console.log('default values for extension set!'));
  });
};

chrome.runtime.onInstalled.addListener(() => {
  initializeExtension();
});

chrome.runtime.onStartup.addListener(() => {
  initializeExtension();
});
