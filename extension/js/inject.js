$(function () {
  console.log('inject.js is loaded.');

  async function getTransactionAddresses(txHash, chain) {
    const { baseServerURL } = await chrome.storage.local.get('baseServerURL');
    const url = `${baseServerURL}/${txHash}/${chain}/addresses`;
    try {
      return await $.ajax({
        url: url,
        async: false,
      });
    } catch (error) {
      console.error(`An error occurred while fetching the info of transaction ${txHash}`);
      console.error(error);
      return;
    }
  }

  async function getTransactionDecodedEvents(txHash, chain, ...addresses) {
    const { baseServerURL } = await chrome.storage.local.get('baseServerURL');
    const url = `${baseServerURL}/${txHash}/${chain}/decode?related_addresses=${addresses.join(',')}`;
    try {
      return await $.ajax({
        url: url,
        async: false,
      });
    } catch (error) {
      console.error(`An error occurred while fetching decoded events of transaction ${txHash}`);
      console.error(error);
      return;
    }
  }

  // gets the icon tag for each event type for Ethereum.
  function getIconForEthereumEvent(e) {
    if (e.event_type === 'spend' && e.event_subtype === 'fee') {
      return '<i class="fa-solid fa-gas-pump"></i>';
    } else if (e.event_type === 'spend') {
      return '<i class="fas fa-inbox-out"></i>';
    } else if (e.event_type === 'receive') {
      return '<i class="fa-solid fa-inbox-in"></i>';
    } else if (e.event_type === 'transfer') {
      return '<i class="fa-sharp fa-regular fa-money-bill-transfer"></i>';
    } else if (e.event_type === 'deposit') {
      return '<i class="fas fa-inbox-in"></i>';
    } else if (e.event_type === 'withdrawal') {
      return '<i class="fas fa-inbox-out"></i>';
    } else {
      return '<i class="fa-solid fa-circle-info"></i>';
    }
  }

  // gets the icon tag for each event type for Optimism.
  function getIconForOptimismAndPolygonEvent(e) {
    if (e.event_type === 'spend' && e.event_subtype === 'fee') {
      return '<i class="fas fa-gas-pump"></i>';
    } else if (e.event_type === 'spend') {
      return '<i class="fas fa-inbox-out"></i>';
    } else if (e.event_type === 'receive') {
      return '<i class="fas fa-inbox-in"></i>';
    } else if (e.event_type === 'transfer') {
      return '<i class="fas fa-exchange"></i>';
    } else if (e.event_type === 'deposit') {
      return '<i class="fas fa-inbox-in"></i>';
    } else if (e.event_type === 'withdrawal') {
      return '<i class="fas fa-inbox-out"></i>';
    } else {
      return '<i class="fas fa-info-circle"></i>';
    }
  }

  function transformAddressesToLinks(text, chain) {
    let url;
    if (chain === 'ethereum') {
      url = 'https://etherscan.io/address';
    } else if (chain === 'optimism') {
      url = 'https://optimistic.etherscan.io/address';
    } else if (chain === 'polygon_pos') {
      url = 'https://polygonscan.com/address';
    }
    const addressRegex = /0x[0-9a-fA-F]{40}/g;
    const etherscanLink = (address) => `<a href="${url}/${address}" target="_blank">${address.slice(0, 8)}...${address.slice(-8)}</a>`;
    return text.replace(addressRegex, etherscanLink);
  }

  async function injectDecodedEventsEthereum(txHash) {
    const chain = 'ethereum';
    $('ul#ContentPlaceHolder1_myTab li:last').before(`
      <li id="ContentPlaceHolder1_li_decodedevents" class="nav-item snap-align-start" role="presentation">
        <a class="nav-link" href="#decodedevents" data-bs-toggle="pill" data-bs-target="#decodedevents-tab-content" aria-controls="decodedevents-tab-content" aria-selected="false" role="tab" tabIndex="-1" onlick="javascript:updatehash('decodedevents');">Decoded Events</a>
      </li>
    `);

    $('div#pills-tabContent').append(`
      <div class="tab-pane fade" id="decodedevents-tab-content" tabIndex="0" role="tabpanel" aria-labelledby="tab-8">
        <div class="card p-5">Fetching data...</div>
      </div>
    `);

    const container = $('div#pills-tabContent').children().last();
    const addresses = await getTransactionAddresses(txHash, chain);
    if (!addresses) {
      container.html(`
        <div class="card pt-5">
          <p class="text-danger" style="padding-left:20px">
            <i class="fa-solid fa-triangle-exclamation" style="padding-right:8px"></i>
            <span>An error occurred while attempting to retrieve transaction addresses. Check console for more errors.</span>
          </p>
        </div>
      `);
      return;
    }

    const decodedEvents = await getTransactionDecodedEvents(txHash, chain, ...addresses.data);
    if (!decodedEvents || decodedEvents?.data?.length === 0) {
      container.html(`
        <div class="card pt-5">
          <p class="text-danger" style="padding-left:20px">
            <i class="fa-solid fa-triangle-exclamation" style="padding-right:8px"></i>
            <span>An error occurred while attempting to retrieve decoded events. Check console for more errors.</span>
          </p>
        </div>
      `);
      return;
    }

    let data = '';
    decodedEvents.data.forEach((el, i) => {
      const icon = getIconForEthereumEvent(el.entry);
      data += `
        <div class="d-flex bg-light rounded border mb-3 mx-3 gap-2 p-3 align-items-baseline">
          ${icon}
          ${transformAddressesToLinks(el.entry.notes, chain)}
        </div>
      `;
      if (i !== decodedEvents.data.length - 1) {
        data += '\n';
      }
    });

    container.html(`
      <div class="card pt-5">
        <h6 style="padding-left:20px;margin-bottom:0">Transaction Receipt Event Logs decoded using <a href="https://rotki.com" target="_blank">rotki</a></h6>
        <hr>
        ${data}
      </div>
    `);
  }

  async function injectDecodedEventsOptimismAndPolygon(txHash, chain) {
    $('ul#nav_tabs').append(`
      <li id="ContentPlaceHolder1_li_decodedevents" class="nav-item">
        <a class="nav-link" id="decodedevents-tab" data-toggle="tab" href="#decodedevents" aria-controls="decodedevents" aria-selected="false" onclick="javascript:updatehash('decodedevents');">Decoded Events</a>
      </li>
    `);

    $('div#myTabContent').append(`
      <div class="tab-pane fade" id="decodedevents" role="tabpanel" aria-labelledby="decodedevents-tab">
        <div class="card-body">Fetching data...</div>
      </div>
    `);

    const container = $('div#myTabContent').children().last();
    const addresses = await getTransactionAddresses(txHash, chain);
    if (!addresses) {
      container.html(`
        <div class="card-body">
          <h6 class="text-danger" style="padding-left:10px">
            <i class="fas fa-exclamation-triangle" style="padding-right:7px"></i>
            <span>An error occurred while attempting to retrieve transaction details. Check console for more errors.</span>
          </h6>
        </div>
      `);
      return;
    }

    const decodedEvents = await getTransactionDecodedEvents(txHash, chain, ...addresses.data);
    if (!decodedEvents || decodedEvents?.data?.length === 0) {
      container.html(`
        <div class="card-body">
          <h6 class="text-danger" style="padding-left:10px">
            <i class="fas fa-exclamation-triangle" style="padding-right:7px"></i>
            <span>An error occurred while attempting to retrieve decoded events. Check console for more errors.</span>
          </h6>
        </div>
      `);
      return;
    }

    let data = '';
    decodedEvents.data.forEach((el, i) => {
      const icon = getIconForOptimismAndPolygonEvent(el.entry);
      data += `
        <div class="bg-light rounded border mb-3 p-3">
          ${icon}
          ${transformAddressesToLinks(el.entry.notes, chain)}
        </div>
      `;
      if (i !== decodedEvents.data.length - 1) {
        data += '\n';
      }
    });

    container.html(`
      <div class="card-body">
        <p class="font-weight-bold text-body" style="margin-bottom:0;padding-bottom:0">Transaction Receipt Event Logs decoded using <a href="https://rotki.com" target="_blank">rotki</a></p>
        <hr>
        ${data}
      </div>
    `);
  }

  // Entrypoint
  const txHash = window.location.pathname.split('/')[2];
  if (window.location.hostname === 'etherscan.io') {
    injectDecodedEventsEthereum(txHash);
  } else if (window.location.host === 'optimistic.etherscan.io') {
    injectDecodedEventsOptimismAndPolygon(txHash, 'optimism');
  } else if (window.location.host === 'polygonscan.com') {
    injectDecodedEventsOptimismAndPolygon(txHash, 'polygon_pos');
  } else {
    return;
  }
});
