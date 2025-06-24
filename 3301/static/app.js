document.addEventListener('DOMContentLoaded', () => {
    // State variables to hold wallet info
    let walletAddress = null;
    let walletPrivateKey = null;

    // References to all the interactive HTML elements
    const generateWalletBtn = document.getElementById('generate-wallet-btn');
    const walletInfoDiv = document.getElementById('wallet-info');
    const walletAddressSpan = document.getElementById('wallet-address');
    const walletPrivateKeySpan = document.getElementById('wallet-private-key');
    const sendTxForm = document.getElementById('send-tx-form');
    const mintForm = document.getElementById('mint-form');
    const refreshChainBtn = document.getElementById('refresh-chain-btn');
    const blockchainViewDiv = document.getElementById('blockchain-view');
    const apiResponseBox = document.getElementById('api-response-box');

    // --- Helper function for API calls ---
    const api = {
        get: async (endpoint) => {
            const response = await fetch(endpoint);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        },
        post: async (endpoint, body) => {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!response.ok) {
                 const errorBody = await response.json();
                 throw new Error(`HTTP error! status: ${response.status}, message: ${errorBody.message || 'Unknown error'}`);
            }
            return response.json();
        }
    };

    const updateResponseBox = (data) => {
        apiResponseBox.textContent = JSON.stringify(data, null, 2);
    };

    // --- Wallet Functions ---
    const generateWallet = async () => {
        try {
            const data = await api.get('/wallet');
            walletAddress = data.public_address;
            walletPrivateKey = data.private_key;

            walletAddressSpan.textContent = walletAddress;
            walletPrivateKeySpan.textContent = walletPrivateKey;
            walletInfoDiv.style.display = 'block';
            updateResponseBox(data);
        } catch (error) {
            console.error("Failed to generate wallet:", error);
            updateResponseBox({ error: error.message });
        }
    };

    // --- Blockchain Functions ---
    const refreshChain = async () => {
        try {
            const data = await api.get('/chain');
            blockchainViewDiv.innerHTML = ''; // Clear previous view
            data.chain.forEach(block => {
                const blockElement = document.createElement('div');
                blockElement.className = 'block-view';
                const content = document.createElement('pre');
                content.textContent = JSON.stringify(block, null, 2);
                blockElement.appendChild(content);
                blockchainViewDiv.appendChild(blockElement);
            });
            updateResponseBox({ message: `Chain refreshed. Length: ${data.length}`});
        } catch (error) {
            console.error("Failed to refresh chain:", error);
            updateResponseBox({ error: error.message });
        }
    };

    // --- Transaction Functions ---
    const sendTransaction = async (event) => {
        event.preventDefault();
        if (!walletAddress || !walletPrivateKey) {
            alert('Please generate a wallet first.');
            return;
        }

        const recipient = document.getElementById('recipient-address').value;
        const amount = parseFloat(document.getElementById('send-amount').value);
        if (!recipient || isNaN(amount) || amount <= 0) {
            alert('Please enter a valid recipient and amount.');
            return;
        }

        try {
            // Step 1: Get the signature from our insecure demo endpoint
            const signPayload = {
                private_key: walletPrivateKey,
                sender: walletAddress,
                recipient: recipient,
                amount: amount,
            };
            const signedData = await api.post('/transactions/sign', signPayload);
            const signature = signedData.signature;

            // Step 2: Send the fully-formed transaction to the network
            const txPayload = {
                sender: walletAddress,
                recipient: recipient,
                amount: amount,
                signature: signature
            };
            const result = await api.post('/transactions/new', txPayload);
            updateResponseBox(result);
            sendTxForm.reset();

        } catch (error) {
            console.error("Transaction failed:", error);
            updateResponseBox({ error: error.message });
        }
    };

    // --- Minting Functions ---
    const mintCoin = async (event) => {
        event.preventDefault();
        if (!walletAddress) {
            alert('Please generate a wallet to receive the mint reward.');
            return;
        }
        const phrase = document.getElementById('secret-phrase').value;
        if (!phrase) {
            alert('Please enter a secret phrase.');
            return;
        }

        try {
            const payload = {
                solver_address: walletAddress,
                secret_phrase: phrase
            };
            const result = await api.post('/mint', payload);
            updateResponseBox(result);
            mintForm.reset();
            // Automatically refresh the chain to see the new block
            if (result.message.includes('New Block Forged')) {
                await refreshChain();
            }
        } catch (error) {
            console.error("Minting failed:", error);
            updateResponseBox({ error: error.message });
        }
    };

    // --- Event Listeners to Connect Functions to Buttons ---
    generateWalletBtn.addEventListener('click', generateWallet);
    refreshChainBtn.addEventListener('click', refreshChain);
    sendTxForm.addEventListener('submit', sendTransaction);
    mintForm.addEventListener('submit', mintCoin);
    
    // --- Initial Actions on Page Load ---
    refreshChain();
});

    // ... (inside the DOMContentLoaded listener) ...

    // --- Add a reference to the new button ---
    const forgeBlockBtn = document.getElementById('forge-block-btn');

    // --- Add the new forging function ---
    const forgeTransactionBlock = async () => {
        if (!walletAddress) {
            alert('Please generate a wallet to receive the forging fees.');
            return;
        }
        console.log("Attempting to forge a new block...");
        try {
            const result = await api.post('/forge', { forger_address: walletAddress });
            updateResponseBox(result);
            // Refresh the chain view to see the new transaction block
            if (result.message.includes('Forged')) {
                await refreshChain();
            }
        } catch (e) {
            handleError("Forging failed", e);
        }
    };

    // --- Add the new event listener ---
    forgeBlockBtn.addEventListener('click', forgeTransactionBlock);

