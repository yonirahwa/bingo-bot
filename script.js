// ============================================================
// BINGO GAME - JAVASCRIPT APPLICATION
// ============================================================

// Configuration
// Telegram Web App Integration
let tg = window.Telegram.WebApp;

// Initialize Telegram Web App
function initTelegramWebApp() {
    if (tg) {
        tg.ready();
        tg.expand();
        
        // Get user info from Telegram
        const user = tg.initDataUnsafe.user;
        if (user) {
            console.log("User from Telegram:", user);
            localStorage.setItem('telegramUserId', user.id);
            localStorage.setItem('telegramUsername', user.username || user.first_name);
        }
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', initTelegramWebApp);

const API_BASE_URL = 'https://bingo-bot-gwg6.onrender.com';
const REFRESH_INTERVAL = 2000; // 2 seconds

// Global State
let gameState = {
    currentScreen: 'gameSelection',
    userId: null,
    username: null,
    balance: 0,
    bonus: 0,
    selectedStake: 0,
    selectedCards: 0,
    gameId: null,
    cardData: [],
    calledNumbers: [],
    autoMark: false,
    gameStartTime: null,
    refreshInterval: null
};

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Get user data from localStorage or session
        const userData = JSON.parse(localStorage.getItem('userData'));
        
        if (!userData) {
            // For demo purposes, create a test user
            initializeDemoUser();
        } else {
            gameState.userId = userData.id;
            gameState.username = userData.username;
            gameState.balance = userData.balance;
            gameState.bonus = userData.bonus_balance;
        }

        // Update UI
        updateUserDisplay();
        
        // Hide loading screen
        setTimeout(() => {
            document.getElementById('loadingScreen').style.display = 'none';
            document.getElementById('mainContainer').style.display = 'block';
        }, 500);

        // Load user stats
        await loadUserStats();

    } catch (error) {
        console.error('Initialization error:', error);
        showError('Failed to initialize application');
    }
});

function initializeDemoUser() {
    gameState.userId = 1;
    gameState.username = 'Player_' + Math.floor(Math.random() * 10000);
    gameState.balance = 1000;
    gameState.bonus = 100;

    const userData = {
        id: gameState.userId,
        username: gameState.username,
        balance: gameState.balance,
        bonus_balance: gameState.bonus
    };

    localStorage.setItem('userData', JSON.stringify(userData));
}

function updateUserDisplay() {
    document.getElementById('usernameBadge').textContent = gameState.username;
    document.getElementById('balanceDisplay').textContent = gameState.balance.toFixed(2) + ' ETB';
    document.getElementById('bonusDisplay').textContent = gameState.bonus.toFixed(2) + ' ETB';
}

async function loadUserStats() {
    try {
        // For demo, use localStorage data
        const stats = JSON.parse(localStorage.getItem('userStats')) || {
            gamesPlayed: 0,
            totalWins: 0,
            totalWinnings: 0
        };

        document.getElementById('gamesPlayedStat').textContent = stats.gamesPlayed;
        document.getElementById('totalWinsStat').textContent = stats.totalWins;
        document.getElementById('totalWinningsStat').textContent = stats.totalWinnings.toFixed(2) + ' ETB';

    } catch (error) {
        console.error('Error loading user stats:', error);
    }
}

// ============================================================
// SCREEN NAVIGATION
// ============================================================

function switchScreen(screenName) {
    // Hide all screens
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });

    // Show selected screen
    const screen = document.getElementById(screenName + 'Screen');
    if (screen) {
        screen.classList.add('active');
        gameState.currentScreen = screenName;
    }
}

function goToGameSelection() {
    switchScreen('gameSelection');
}

function goToCardSelection() {
    switchScreen('cardSelection');
}

function goToGamePlay() {
    switchScreen('gamePlay');
}

function goToProfile() {
    loadProfileData();
    switchScreen('profile');
}

function goToWallet() {
    loadWalletData();
    switchScreen('wallet');
}

function goToLeaderboard() {
    loadLeaderboardData();
    switchScreen('leaderboard');
}

function goBack() {
    goToGameSelection();
}

// ============================================================
// GAME SELECTION
// ============================================================

function selectStake(amount) {
    gameState.selectedStake = amount;
    console.log('Selected stake:', amount, 'ETB');
    
    // Check if user has sufficient balance
    if (gameState.balance < amount) {
        showError('Insufficient balance! Please add funds to your wallet.');
        return;
    }

    goToCardSelection();
}

// ============================================================
// CARD SELECTION
// ============================================================

function selectCards(count) {
    gameState.selectedCards = count;
    console.log('Selected cards:', count);
    
    // Initialize game
    initializeGame();
    goToGamePlay();
}

// ============================================================
// GAME INITIALIZATION
// ============================================================

function initializeGame() {
    gameState.gameStartTime = new Date();
    gameState.calledNumbers = [];
    gameState.cardData = [];

    // Generate bingo cards
    for (let i = 0; i < gameState.selectedCards; i++) {
        gameState.cardData.push(generateBingoCard(i + 1));
    }

    // Deduct stake from balance
    gameState.balance -= gameState.selectedStake;
    updateUserDisplay();

    // Create game ID
    gameState.gameId = 'GAME_' + Date.now();

    // Render cards
    renderBingoCards();

    // Update game info
    document.getElementById('gameIdDisplay').textContent = gameState.gameId;
    document.getElementById('stakeDisplay').textContent = gameState.selectedStake + ' ETB';
    document.getElementById('gameStatusDisplay').textContent = 'Active';

    // Start updating called numbers
    startGameUpdates();

    // Update leaderboard
    updateLeaderboardDisplay();
}

function generateBingoCard(cardNumber) {
    const card = {
        number: cardNumber,
        numbers: [],
        markedNumbers: []
    };

    // Generate 75 unique random numbers (1-75)
    const allNumbers = Array.from({ length: 75 }, (_, i) => i + 1);
    card.numbers = allNumbers.sort(() => Math.random() - 0.5);

    return card;
}

function renderBingoCards() {
    const container = document.getElementById('cardsContainer');
    container.innerHTML = '';

    gameState.cardData.forEach((card, index) => {
        const cardEl = document.createElement('div');
        cardEl.className = 'bingo-card';
        cardEl.innerHTML = `
            <div class="card-title">Card ${card.number}</div>
            <div class="card-grid" id="cardGrid-${index}"></div>
        `;

        const gridEl = cardEl.querySelector(`#cardGrid-${index}`);

        // Add 75 numbers to the grid
        card.numbers.forEach((number, cellIndex) => {
            const cell = document.createElement('div');
            cell.className = 'number-cell';
            cell.textContent = number;
            cell.dataset.cardIndex = index;
            cell.dataset.cellIndex = cellIndex;
            cell.dataset.number = number;

            // Check if already marked
            if (card.markedNumbers.includes(number)) {
                cell.classList.add('marked');
            }

            // Add click handler
            cell.addEventListener('click', () => toggleNumberMark(index, number, cell));

            gridEl.appendChild(cell);
        });

        container.appendChild(cardEl);
    });
}

function toggleNumberMark(cardIndex, number, cellElement) {
    const card = gameState.cardData[cardIndex];
    
    if (card.markedNumbers.includes(number)) {
        // Unmark
        card.markedNumbers = card.markedNumbers.filter(n => n !== number);
        cellElement.classList.remove('marked');
    } else {
        // Mark
        card.markedNumbers.push(number);
        cellElement.classList.add('marked');
    }

    // Check for bingo
    checkForBingo();
}

function checkForBingo() {
    // Check if any card has all 75 numbers marked
    const hasWinner = gameState.cardData.some(card => card.markedNumbers.length === 75);

    if (hasWinner) {
        document.getElementById('bingoBtn').style.display = 'block';
    } else {
        document.getElementById('bingoBtn').style.display = 'none';
    }
}

// ============================================================
// GAME UPDATES
// ============================================================

function startGameUpdates() {
    // Simulate calling numbers
    simulateCalledNumbers();

    // Update called numbers display
    updateCalledNumbersDisplay();

    // Start refresh interval
    if (gameState.refreshInterval) {
        clearInterval(gameState.refreshInterval);
    }

    gameState.refreshInterval = setInterval(() => {
        updateCalledNumbersDisplay();
        updateGameTimer();
    }, REFRESH_INTERVAL);
}

function simulateCalledNumbers() {
    // Simulate calling random numbers
    if (gameState.calledNumbers.length < 75) {
        const allNumbers = Array.from({ length: 75 }, (_, i) => i + 1);
        const notCalled = allNumbers.filter(n => !gameState.calledNumbers.includes(n));
        
        if (notCalled.length > 0) {
            const randomNumber = notCalled[Math.floor(Math.random() * notCalled.length)];
            gameState.calledNumbers.push(randomNumber);

            // Auto-mark if enabled
            if (gameState.autoMark) {
                autoMarkNumber(randomNumber);
            }
        }
    }
}

function autoMarkNumber(number) {
    gameState.cardData.forEach((card, cardIndex) => {
        if (card.numbers.includes(number) && !card.markedNumbers.includes(number)) {
            card.markedNumbers.push(number);

            // Update UI
            const cell = document.querySelector(
                `[data-cardIndex="${cardIndex}"][data-number="${number}"]`
            );
            if (cell) {
                cell.classList.add('marked');
            }
        }
    });

    checkForBingo();
}

function updateCalledNumbersDisplay() {
    const list = document.getElementById('calledNumbersList');
    
    if (gameState.calledNumbers.length === 0) {
        list.innerHTML = '<p class="empty-message">Waiting for numbers...</p>';
    } else {
        list.innerHTML = gameState.calledNumbers.map(num => 
            `<div class="called-number">${num}</div>`
        ).join('');
    }

    // Update counts
    document.getElementById('calledCount').textContent = gameState.calledNumbers.length;
    document.getElementById('remainingCount').textContent = 75 - gameState.calledNumbers.length;
}

function updateGameTimer() {
    if (gameState.gameStartTime) {
        const elapsed = Math.floor((Date.now() - gameState.gameStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;

        document.getElementById('timeElapsedDisplay').textContent = 
            `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    // Continue simulating calls
    simulateCalledNumbers();
}

function toggleAutoMark() {
    gameState.autoMark = !gameState.autoMark;
    document.getElementById('autoMarkText').textContent = 
        '🔘 Auto Mark: ' + (gameState.autoMark ? 'ON' : 'OFF');
}

// ============================================================
// BINGO & WIN
// ============================================================

function claimBingo() {
    // Calculate winnings
    const winnings = gameState.selectedStake * 10; // 10x multiplier for demo
    gameState.balance += winnings;

    // Update stats
    const stats = JSON.parse(localStorage.getItem('userStats')) || {
        gamesPlayed: 0,
        totalWins: 0,
        totalWinnings: 0
    };

    stats.totalWins++;
    stats.totalWinnings += winnings;
    stats.gamesPlayed++;

    localStorage.setItem('userStats', JSON.stringify(stats));
    updateUserDisplay();

    // Show win modal
    showWinModal(winnings);

    // End game
    endGameSession();
}

function showWinModal(amount) {
    document.getElementById('winAmount').textContent = '+' + amount.toFixed(2) + ' ETB';
    document.getElementById('winModal').style.display = 'flex';
}

function closeWinModal() {
    document.getElementById('winModal').style.display = 'none';
    goToGameSelection();
}

function endGame() {
    if (confirm('Are you sure you want to end this game?')) {
        endGameSession();
    }
}

function endGameSession() {
    // Stop game updates
    if (gameState.refreshInterval) {
        clearInterval(gameState.refreshInterval);
    }

    // Reset game state
    gameState.gameId = null;
    gameState.cardData = [];
    gameState.calledNumbers = [];
    gameState.autoMark = false;

    // Return to game selection
    goToGameSelection();
}

// ============================================================
// PROFILE MANAGEMENT
// ============================================================

async function loadProfileData() {
    try {
        // Get user data from localStorage
        const userData = JSON.parse(localStorage.getItem('userData'));
        const stats = JSON.parse(localStorage.getItem('userStats')) || {
            gamesPlayed: 0,
            totalWins: 0,
            totalWinnings: 0
        };

        // Format member since date
        const memberSince = localStorage.getItem('memberSinceDate') || new Date().toLocaleDateString();

        // Update profile UI
        document.getElementById('profileUsername').textContent = gameState.username;
        document.getElementById('profilePhone').textContent = userData?.phone || 'Not provided';
        document.getElementById('profileMemberSince').textContent = memberSince;
        document.getElementById('profileBalance').textContent = gameState.balance.toFixed(2) + ' ETB';

        // Update stats
        document.getElementById('profileGamesPlayed').textContent = stats.gamesPlayed;
        document.getElementById('profileTotalWins').textContent = stats.totalWins;

        // Calculate win rate
        const winRate = stats.gamesPlayed > 0 
            ? Math.round((stats.totalWins / stats.gamesPlayed) * 100) 
            : 0;
        document.getElementById('profileWinRate').textContent = winRate + '%';

    } catch (error) {
        console.error('Error loading profile data:', error);
        showError('Failed to load profile data');
    }
}

async function updateProfileData(profileInfo) {
    try {
        // Save to localStorage
        const userData = JSON.parse(localStorage.getItem('userData'));
        userData.phone = profileInfo.phone;
        localStorage.setItem('userData', JSON.stringify(userData));

        showSuccess('Profile updated successfully!');
        loadProfileData();

    } catch (error) {
        console.error('Error updating profile:', error);
        showError('Failed to update profile');
    }
}

// ============================================================
// WALLET MANAGEMENT
// ============================================================

async function loadWalletData() {
    try {
        document.getElementById('walletBalance').textContent = gameState.balance.toFixed(2) + ' ETB';
        document.getElementById('walletBonus').textContent = gameState.bonus.toFixed(2) + ' ETB';

        // Load transaction history
        loadTransactionHistory();

    } catch (error) {
        console.error('Error loading wallet data:', error);
        showError('Failed to load wallet data');
    }
}

function showDepositForm() {
    document.getElementById('formTitle').textContent = '💸 Deposit Funds';
    document.getElementById('transactionType').value = 'deposit';
    document.getElementById('transactionForm').style.display = 'block';
    document.getElementById('transactionAmount').value = '';
    document.getElementById('transactionMethod').value = '';
    document.getElementById('transactionDescription').value = '';
}

function showWithdrawForm() {
    document.getElementById('formTitle').textContent = '💳 Withdraw Funds';
    document.getElementById('transactionType').value = 'withdraw';
    document.getElementById('transactionForm').style.display = 'block';
    document.getElementById('transactionAmount').value = '';
    document.getElementById('transactionMethod').value = '';
    document.getElementById('transactionDescription').value = '';
}

function showTransferForm() {
    document.getElementById('formTitle').textContent = '🔄 Transfer Funds';
    document.getElementById('transactionType').value = 'transfer';
    document.getElementById('transactionForm').style.display = 'block';
    document.getElementById('transactionAmount').value = '';
    document.getElementById('transactionMethod').value = '';
    document.getElementById('transactionDescription').value = '';
}

function hideTransactionForm() {
    document.getElementById('transactionForm').style.display = 'none';
}

async function processTransaction(event) {
    event.preventDefault();

    try {
        const type = document.getElementById('transactionType').value;
        const amount = parseFloat(document.getElementById('transactionAmount').value);
        const method = document.getElementById('transactionMethod').value;
        const description = document.getElementById('transactionDescription').value;

        // Validation
        if (amount <= 0) {
            showError('Please enter a valid amount');
            return;
        }

        if (!method) {
            showError('Please select a payment method');
            return;
        }

        // Check balance for withdraw and transfer
        if ((type === 'withdraw' || type === 'transfer') && amount > gameState.balance) {
            showError('Insufficient balance for this transaction');
            return;
        }

        // Create transaction object
        const transaction = {
            id: 'TXN_' + Date.now(),
            type: type,
            amount: amount,
            method: method,
            description: description,
            status: 'pending',
            timestamp: new Date().toISOString(),
            userId: gameState.userId
        };

        // Process transaction
        await saveTransaction(transaction);

        // Update balance
        if (type === 'deposit') {
            gameState.balance += amount;
        } else if (type === 'withdraw' || type === 'transfer') {
            gameState.balance -= amount;
        }

        updateUserDisplay();
        hideTransactionForm();
        loadWalletData();

        showSuccess(`${type.charAt(0).toUpperCase() + type.slice(1)} of ${amount.toFixed(2)} ETB processed successfully!`);

    } catch (error) {
        console.error('Error processing transaction:', error);
        showError('Failed to process transaction');
    }
}

async function saveTransaction(transaction) {
    try {
        // Get existing transactions
        const transactions = JSON.parse(localStorage.getItem('transactions')) || [];
        
        // Add new transaction
        transactions.unshift(transaction);

        // Keep only last 50 transactions
        const limitedTransactions = transactions.slice(0, 50);

        // Save to localStorage
        localStorage.setItem('transactions', JSON.stringify(limitedTransactions));

    } catch (error) {
        console.error('Error saving transaction:', error);
        throw error;
    }
}

function loadTransactionHistory() {
    try {
        const transactions = JSON.parse(localStorage.getItem('transactions')) || [];
        const container = document.getElementById('transactionsList');

        if (transactions.length === 0) {
            container.innerHTML = '<p class="empty-message">No transactions yet</p>';
            return;
        }

        container.innerHTML = transactions.map(txn => `
            <div class="transaction-item">
                <div class="transaction-info">
                    <div class="transaction-type">
                        ${getTransactionIcon(txn.type)} ${txn.type.charAt(0).toUpperCase() + txn.type.slice(1)}
                    </div>
                    <div class="transaction-date">
                        ${new Date(txn.timestamp).toLocaleString()} • ${txn.method}
                    </div>
                </div>
                <div class="transaction-amount ${txn.type}">
                    ${txn.type === 'deposit' ? '+' : '-'}${txn.amount.toFixed(2)} ETB
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading transaction history:', error);
    }
}

function getTransactionIcon(type) {
    const icons = {
        deposit: '💸',
        withdraw: '💳',
        transfer: '🔄'
    };
    return icons[type] || '💰';
}

// ============================================================
// LEADERBOARD MANAGEMENT
// ============================================================

async function loadLeaderboardData() {
    try {
        // For demo, generate sample leaderboard data
        const leaderboardData = generateSampleLeaderboard();
        displayLeaderboard(leaderboardData);

    } catch (error) {
        console.error('Error loading leaderboard:', error);
        showError('Failed to load leaderboard');
    }
}

function generateSampleLeaderboard() {
    const players = [
        { rank: 1, name: 'Champion_Pro', wins: 45, balance: 5230.50 },
        { rank: 2, name: 'LuckyPlayer', wins: 38, balance: 4150.25 },
        { rank: 3, name: 'BingoMaster', wins: 35, balance: 3890.75 },
        { rank: 4, name: 'WinStreak', wins: 32, balance: 3420.00 },
        { rank: 5, name: 'GoldenCard', wins: 28, balance: 2980.50 },
        { rank: 6, name: 'Lucky77', wins: 25, balance: 2650.25 },
        { rank: 7, name: 'Ace_Player', wins: 22, balance: 2340.75 },
        { rank: 8, name: 'Diamond_Star', wins: 20, balance: 2120.00 },
        { rank: 9, name: 'Swift_Marker', wins: 18, balance: 1890.50 },
        { rank: 10, name: 'Card_Wizard', wins: 15, balance: 1620.25 },
        { rank: 11, name: 'BingoKing', wins: 14, balance: 1520.00 },
        { rank: 12, name: 'Lucky_One', wins: 12, balance: 1350.75 },
        { rank: 13, name: 'Star_Player', wins: 11, balance: 1240.50 },
        { rank: 14, name: 'Pro_Gamer', wins: 10, balance: 1120.25 },
        { rank: 15, name: 'Card_Master', wins: 9, balance: 980.00 },
        { rank: 16, name: 'Quick_Mark', wins: 8, balance: 890.50 },
        { rank: 17, name: 'Bingo_Star', wins: 7, balance: 750.25 },
        { rank: 18, name: 'Winner_123', wins: 6, balance: 620.75 },
        { rank: 19, name: 'Lucky_Day', wins: 5, balance: 520.00 },
        { rank: 20, name: 'Card_Lover', wins: 4, balance: 420.50 }
    ];

    return players;
}

function displayLeaderboard(data) {
    const container = document.getElementById('leaderboardFullList');

    if (!data || data.length === 0) {
        container.innerHTML = '<p class="empty-message">No leaderboard data available</p>';
        return;
    }

    container.innerHTML = data.map(player => {
        let rankClass = '';
        if (player.rank === 1) rankClass = 'gold';
        else if (player.rank === 2) rankClass = 'silver';
        else if (player.rank === 3) rankClass = 'bronze';

        return `
            <div class="leaderboard-row">
                <div class="lb-rank ${rankClass}">
                    ${getRankMedal(player.rank)} #${player.rank}
                </div>
                <div class="lb-name">${player.name}</div>
                <div class="lb-wins">${player.wins} wins</div>
                <div class="lb-balance">${player.balance.toFixed(2)} ETB</div>
            </div>
        `;
    }).join('');
}

function getRankMedal(rank) {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return '🎖️';
}

function updateLeaderboardDisplay() {
    try {
        // Mini leaderboard in game screen
        const leaderboardData = generateSampleLeaderboard().slice(0, 5);
        const container = document.getElementById('leaderboardList');

        if (!container) return;

        container.innerHTML = leaderboardData.map(player => `
            <div class="leaderboard-item">
                <span class="leaderboard-rank">${getRankMedal(player.rank)} #${player.rank}</span>
                <span class="leaderboard-name">${player.name}</span>
                <span class="leaderboard-balance">${player.balance.toFixed(0)} ETB</span>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error updating leaderboard display:', error);
    }
}

// ============================================================
// ERROR & SUCCESS MODALS
// ============================================================

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorModal').style.display = 'flex';
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        closeErrorModal();
    }, 5000);
}

function closeErrorModal() {
    document.getElementById('errorModal').style.display = 'none';
}

function showSuccess(message) {
    // Create temporary success notification
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: linear-gradient(135deg, #10b981, #34d399);
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        font-weight: 600;
        z-index: 3000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = '✓ ' + message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// ============================================================
// API INTEGRATION (Ready for backend)
// ============================================================

async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
            }
        };

        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        return await response.json();

    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function createGame(stake, cardCount) {
    try {
        const gameData = {
            userId: gameState.userId,
            stake: stake,
            cardCount: cardCount,
            status: 'active',
            createdAt: new Date().toISOString()
        };

        const response = await apiCall('/games', 'POST', gameData);
        return response;

    } catch (error) {
        console.error('Error creating game:', error);
        throw error;
    }
}

async function updateGameStatus(gameId, status) {
    try {
        const response = await apiCall(`/games/${gameId}`, 'PUT', { status: status });
        return response;

    } catch (error) {
        console.error('Error updating game status:', error);
        throw error;
    }
}

async function submitBingo(gameId, winnings) {
    try {
        const response = await apiCall(`/games/${gameId}/bingo`, 'POST', {
            winnings: winnings,
            timestamp: new Date().toISOString()
        });
        return response;

    } catch (error) {
        console.error('Error submitting bingo:', error);
        throw error;
    }
}

async function getGameHistory() {
    try {
        const response = await apiCall(`/users/${gameState.userId}/games`);
        return response;

    } catch (error) {
        console.error('Error fetching game history:', error);
        return [];
    }
}

async function getTopPlayers(limit = 20) {
    try {
        const response = await apiCall(`/leaderboard?limit=${limit}`);
        return response;

    } catch (error) {
        console.error('Error fetching leaderboard:', error);
        return [];
    }
}

async function processDeposit(amount, method, description) {
    try {
        const response = await apiCall('/transactions/deposit', 'POST', {
            userId: gameState.userId,
            amount: amount,
            method: method,
            description: description,
            timestamp: new Date().toISOString()
        });
        return response;

    } catch (error) {
        console.error('Error processing deposit:', error);
        throw error;
    }
}

async function processWithdraw(amount, method, accountDetails) {
    try {
        const response = await apiCall('/transactions/withdraw', 'POST', {
            userId: gameState.userId,
            amount: amount,
            method: method,
            accountDetails: accountDetails,
            timestamp: new Date().toISOString()
        });
        return response;

    } catch (error) {
        console.error('Error processing withdrawal:', error);
        throw error;
    }
}

async function getBalance() {
    try {
        const response = await apiCall(`/users/${gameState.userId}/balance`);
        gameState.balance = response.balance;
        gameState.bonus = response.bonus;
        updateUserDisplay();
        return response;

    } catch (error) {
        console.error('Error fetching balance:', error);
        return null;
    }
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-ET', {
        style: 'currency',
        currency: 'ETB',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-ET', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);
    let interval = seconds / 31536000;

    if (interval > 1) return Math.floor(interval) + 'y ago';
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + 'mo ago';
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + 'd ago';
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + 'h ago';
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + 'min ago';
    return Math.floor(seconds) + 's ago';
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhoneNumber(phone) {
    const re = /^(\+251|0)[1-9]\d{8}$/;
    return re.test(phone);
}

function maskPhoneNumber(phone) {
    if (!phone) return '';
    const cleaned = phone.replace(/\D/g, '');
    return cleaned.slice(0, -4).replace(/\d/g, '*') + cleaned.slice(-4);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function playSound(soundName) {
    // Create audio context for sound effects
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        switch (soundName) {
            case 'success':
                oscillator.frequency.value = 800;
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.1);
                break;

            case 'error':
                oscillator.frequency.value = 300;
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.2);
                break;

            case 'click':
                oscillator.frequency.value = 600;
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.05);
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.05);
                break;

            case 'bingo':
                for (let i = 0; i < 3; i++) {
                    const osc = audioContext.createOscillator();
                    const gain = audioContext.createGain();
                    osc.connect(gain);
                    gain.connect(audioContext.destination);
                    osc.frequency.value = 800 + (i * 200);
                    gain.gain.setValueAtTime(0.2, audioContext.currentTime + (i * 0.15));
                    gain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + (i * 0.15) + 0.15);
                    osc.start(audioContext.currentTime + (i * 0.15));
                    osc.stop(audioContext.currentTime + (i * 0.15) + 0.15);
                }
                break;
        }
    } catch (error) {
        console.log('Sound not supported:', error);
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showSuccess('Copied to clipboard!');
    }).catch(() => {
        showError('Failed to copy to clipboard');
    });
}

function openInNewTab(url) {
    window.open(url, '_blank', 'noopener,noreferrer');
}

// ============================================================
// EVENT LISTENERS & PAGE VISIBILITY
// ============================================================

document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden
        if (gameState.refreshInterval) {
            clearInterval(gameState.refreshInterval);
        }
    } else {
        // Page is visible
        if (gameState.currentScreen === 'gamePlay') {
            startGameUpdates();
        }
    }
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (gameState.gameId) {
        // Save game state before closing
        localStorage.setItem('activeGame', JSON.stringify({
            gameId: gameState.gameId,
            timestamp: Date.now()
        }));
    }
});

// Handle online/offline
window.addEventListener('online', () => {
    console.log('Connection restored');
    showSuccess('Connection restored!');
    loadUserStats();
});

window.addEventListener('offline', () => {
    console.log('Connection lost');
    showError('No internet connection. Some features may be unavailable.');
});

// Keyboard shortcuts
document.addEventListener('keydown', (event) => {
    if (event.ctrlKey || event.metaKey) {
        if (event.key === 's') {
            event.preventDefault();
            // Save game state
        }
        if (event.key === 'b') {
            event.preventDefault();
            if (gameState.currentScreen === 'gamePlay') {
                document.getElementById('bingoBtn').click();
            }
        }
    }

    // Escape key to go back
    if (event.key === 'Escape') {
        if (gameState.currentScreen !== 'gameSelection') {
            goBack();
        }
    }
});

// ============================================================
// RESPONSIVE DESIGN HELPERS
// ============================================================

function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

function adjustLayoutForDevice() {
    if (isMobileDevice()) {
        document.body.classList.add('mobile-device');
        
        // Adjust game container for mobile
        const gameContainer = document.querySelector('.game-container');
        if (gameContainer) {
            gameContainer.style.gridTemplateColumns = '1fr';
        }
    }
}

// Call on load
adjustLayoutForDevice();

// Handle window resize
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        adjustLayoutForDevice();
    }, 250);
});

// ============================================================
// EXPORT FUNCTIONS FOR EXTERNAL USE
// ============================================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        gameState,
        selectStake,
        selectCards,
        claimBingo,
        endGame,
        loadProfileData,
        loadWalletData,
        loadLeaderboardData,
        apiCall,
        showError,
        showSuccess
    };
}