document.addEventListener('DOMContentLoaded', () => {
    // Element References
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const resultsSection = document.getElementById('results-section');
    const resultsView = document.getElementById('results-view');
    const latestBlocksView = document.getElementById('latest-blocks-view');

    // --- API Helper ---
    const apiGet = async (endpoint) => {
        const response = await fetch(endpoint);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }
        return response.json();
    };

    // --- Display Functions ---
    const displayError = (message) => {
        resultsView.innerHTML = `<p class="warning">Error: ${message}</p>`;
        resultsSection.style.display = 'block';
    };

    const displayAddressData = (data) => {
        let transactionsHtml = '<h4>Transactions:</h4>';
        if (data.transactions.length === 0) {
            transactionsHtml += '<p>No transactions found for this address.</p>';
        } else {
            data.transactions.forEach(tx => {
                transactionsHtml += `<pre>${JSON.stringify(tx, null, 2)}</pre>`;
            });
        }

        resultsView.innerHTML = `
            <h3>Address: ${data.address}</h3>
            <p><strong>Balance:</strong> ${data.balance} C3301</p>
            <p><strong>Total Transactions:</strong> ${data.transaction_count}</p>
            <hr>
            ${transactionsHtml}
        `;
        resultsSection.style.display = 'block';
    };

    const loadLatestBlocks = async () => {
        try {
            const data = await apiGet('/chain');
            latestBlocksView.innerHTML = ''; // Clear previous view
            // Show latest 5 blocks, or all if less than 5
            const recentBlocks = data.chain.slice(-5).reverse();
            recentBlocks.forEach(block => {
                const blockElement = document.createElement('div');
                blockElement.className = 'block-view';
                blockElement.innerHTML = `
                    <h4>Block #${block.index}</h4>
                    <pre>${JSON.stringify(block, null, 2)}</pre>
                `;
                latestBlocksView.appendChild(blockElement);
            });
        } catch (error) {
            latestBlocksView.innerHTML = `<p class="warning">Could not load chain data.</p>`;
            console.error(error);
        }
    };
    
    // --- Event Handlers ---
    const handleSearch = async (event) => {
        event.preventDefault();
        const query = searchInput.value.trim();
        if (!query) return;

        try {
            const data = await apiGet(`/address/${query}`);
            displayAddressData(data);
        } catch (error) {
            displayError(`Failed to fetch data for address "${query}". ${error.message}`);
            console.error(error);
        }
    };

    // --- Initial Load ---
    searchForm.addEventListener('submit', handleSearch);
    loadLatestBlocks();
});
