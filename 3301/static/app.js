document.addEventListener('DOMContentLoaded', () => {
    let walletAddress = null, walletPrivateKey = null;
    const elements = {
        generateWalletBtn: document.getElementById('generate-wallet-btn'),
        walletInfoDiv: document.getElementById('wallet-info'),
        walletAddressSpan: document.getElementById('wallet-address'),
        walletPrivateKeySpan: document.getElementById('wallet-private-key'),
        sendTxForm: document.getElementById('send-tx-form'),
        mintForm: document.getElementById('mint-form'),
        refreshChainBtn: document.getElementById('refresh-chain-btn'),
        blockchainViewDiv: document.getElementById('blockchain-view'),
        apiResponseBox: document.getElementById('api-response-box')
    };
    const api = {
        get: async (endpoint) => { const r = await fetch(endpoint); if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`); return r.json(); },
        post: async (endpoint, body) => { const r = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); if (!r.ok) { const e = await r.json(); throw new Error(`HTTP error! status: ${r.status}, message: ${e.message||'Unknown'}`); } return r.json(); }
    };
    const updateResponseBox = data => { elements.apiResponseBox.textContent = JSON.stringify(data, null, 2); };
    const handleError = (context, error) => { console.error(`${context}:`, error); updateResponseBox({ error: error.message }); };
    const generateWallet = async () => { try { const data = await api.get('/wallet'); walletAddress = data.public_address; walletPrivateKey = data.private_key; elements.walletAddressSpan.textContent = walletAddress; elements.walletPrivateKeySpan.textContent = walletPrivateKey; elements.walletInfoDiv.style.display = 'block'; updateResponseBox(data); } catch (e) { handleError("Failed to generate wallet", e); } };
    const refreshChain = async () => { try { const data = await api.get('/chain'); elements.blockchainViewDiv.innerHTML = ''; const latestBlock = data.chain.slice(-1)[0]; const blockEl = document.createElement('div'); blockEl.className = 'block-view'; const content = document.createElement('pre'); content.textContent = JSON.stringify(latestBlock, null, 2); blockEl.appendChild(content); elements.blockchainViewDiv.appendChild(blockEl); updateResponseBox({ message: `Chain refreshed. Length: ${data.length}` }); } catch (e) { handleError("Failed to refresh chain", e); } };
    
    // REWRITTEN to handle timestamp correctly
    const sendTransaction = async (event) => {
        event.preventDefault();
        if (!walletAddress) return alert('Please generate a wallet first.');
        const recipient = document.getElementById('recipient-address').value;
        const amount = parseFloat(document.getElementById('send-amount').value);
        if (!recipient || isNaN(amount) || amount <= 0) return alert('Please enter a valid recipient and amount.');

        // 1. Generate the timestamp ONCE, here in the browser.
        const timestamp = Date.now() / 1000.0;

        try {
            // 2. Send the timestamp to the signing endpoint.
            const signPayload = {
                private_key: walletPrivateKey,
                sender: walletAddress,
                recipient: recipient,
                amount: amount,
                timestamp: timestamp
            };
            const signedData = await api.post('/transactions/sign', signPayload);
            const signature = signedData.signature;

            // 3. Send the SAME timestamp to the new transaction endpoint.
            const txPayload = {
                sender: walletAddress,
                recipient: recipient,
                amount: amount,
                signature: signature,
                timestamp: timestamp
            };
            const result = await api.post('/transactions/new', txPayload);
            updateResponseBox(result);
            elements.sendTxForm.reset();

        } catch (e) {
            handleError("Transaction failed", e);
        }
    };

    const mintCoin = async (event) => { event.preventDefault(); if (!walletAddress) return alert('Please generate a wallet to receive the mint reward.'); const phrase = document.getElementById('secret-phrase').value; if (!phrase) return alert('Please enter a secret phrase.'); try { const result = await api.post('/mint', { solver_address: walletAddress, secret_phrase: phrase }); updateResponseBox(result); elements.mintForm.reset(); if (result.message.includes('New Block Forged')) await refreshChain(); } catch (e) { handleError("Minting failed", e); } };
    elements.generateWalletBtn.addEventListener('click', generateWallet);
    elements.refreshChainBtn.addEventListener('click', refreshChain);
    elements.sendTxForm.addEventListener('submit', sendTransaction);
    elements.mintForm.addEventListener('submit', mintCoin);
    refreshChain();
});
