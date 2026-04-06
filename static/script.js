document.addEventListener('DOMContentLoaded', () => {
    // --- Global State ---
    const state = {
        gameData: null,
        audioUnlocked: false,
        missionSlots: [],
        unlockedTiers: {},
        scoreHistory: [],
        upgrades: { tree: {}, purchased: [], round_number: 0 },
        allPlayerUpgrades: {},
        allPlayerMissions: {},
        confirmCallback: null,
        branchesConfirmCallback: null,
        missionChoiceContext: null,
        factionData: { factions: {}, taken: [] },
        upgradeOwnership: {},
        gameState: null,
        sessionTimerInterval: null,
        playerTimerInterval: null,
        warningSoundPlayed: false,
        timerWarningSound: new Audio('/static/timer.mp3'),
        timerEndSound: new Audio('/static/alarm.mp3'),
    };
    state.timerEndSound.loop = true;

    // --- DOM Element Cache ---
    const DOMElements = {
        screens: {
            login: document.getElementById('login-screen'),
            mainMenu: document.getElementById('main-menu-screen'),
            mission: document.getElementById('mission-screen'),
            score: document.getElementById('score-screen'),
            news: document.getElementById('news-screen'),
            upgrades: document.getElementById('upgrades-screen'),
            timer: document.getElementById('timer-screen'),
        },
        login: {
            nicknameInput: document.getElementById('nickname-input'),
            factionSelect: document.getElementById('faction-select'),
            loginButton: document.querySelector('#login-screen .login-button'),
            loginMessage: document.getElementById('login-message'),
        },
        mainMenu: {
            userInfo: document.getElementById('main-menu-user-info'),
            missionButton: document.getElementById('mission-button'),
            yebalyButton: document.getElementById('yebaly-button'),
            newsButton: document.getElementById('news-button'),
            upgradesButton: document.getElementById('upgrades-button'),
            logoutButton: document.getElementById('logout-button'),
            resetButton: document.getElementById('reset-game-button'),
        },
        mission: {
            backButton: document.getElementById('mission-back-button'),
            branchesButton: document.getElementById('mission-branches-button'),
            viewPlayersMissionsButton: document.getElementById('view-players-missions-button'),
            userInfo: document.getElementById('mission-screen-user-info'),
            currentUser: document.getElementById('current-user-mission-screen'),
            level1Score: document.getElementById('mission-stat-i'),
            level2Score: document.getElementById('mission-stat-ii'),
            level3Score: document.getElementById('mission-stat-iii'),
            scrollArea: document.getElementById('missions-scroll-area'),
        },
        news: {
            backButton: document.getElementById('news-back-button'),
            roundIndicator: document.getElementById('round-indicator'),
            scrollArea: document.getElementById('news-scroll-area'),
            resetButton: document.getElementById('reset-news-button'),
            initiativeScreen: document.getElementById('initiative-screen'),
            initiativeSetupView: document.getElementById('initiative-setup-view'),
            initiativePlayerOrderSelection: document.getElementById('initiative-player-order-selection'),
            initiativeConfirmButton: document.getElementById('initiative-confirm-button'),
            determineInitiativeView: document.getElementById('determine-initiative-view'),
            determineInitiativeTitle: document.getElementById('determine-initiative-title'),
            determineInitiativeButton: document.getElementById('determine-initiative-button'),
            initiativeResultView: document.getElementById('initiative-result-view'),
            initiativeResultDisplay: document.getElementById('initiative-result-display'),
            initiativeNextNewsButton: document.getElementById('initiative-next-news-button'),
            newsContentWrapper: document.getElementById('news-content-wrapper'),
        },
        upgrades: {
            backButton: document.getElementById('upgrades-back-button'),
            pointsDisplay: document.getElementById('upgrades-points-display'),
            treeContainer: document.getElementById('upgrade-tree-container'),
            limitsDisplay: document.getElementById('upgrades-limits-display'),
            viewPlayersButton: document.getElementById('view-players-upgrades-button'),
        },
        timer: {
            backButton: document.getElementById('timer-back-button'),
            roundInfo: document.getElementById('timer-round-info'),
            sessionTimerDisplay: document.getElementById('session-timer-display'),
            playerTurnSection: document.getElementById('player-turn-section'),
            botTurnSection: document.getElementById('bot-turn-section'),
            playerTurnTitle: document.getElementById('player-turn-title'),
            playerTimerDisplay: document.getElementById('player-timer-display'),
            startPauseButton: document.getElementById('timer-start-pause-button'),
            nextPlayerButton: document.getElementById('timer-next-player-button'),
            actionPointsSection: document.getElementById('action-points-section'),
            activePointsValue: document.getElementById('active-points-value'),
            attackPointsValue: document.getElementById('attack-points-value'),
            buildPointsValue: document.getElementById('build-points-value'),
        },
        headerTimers: {
            main: document.getElementById('header-timer-button'),
            mission: document.getElementById('mission-header-timer'),
            score: document.getElementById('score-header-timer'),
            news: document.getElementById('news-header-timer'),
            upgrades: document.getElementById('upgrades-header-timer'),
        },
        score: {
            backButton: document.getElementById('score-back-button'),
            topPlayersList: document.getElementById('top-players-list'),
            historyPreviewContainer: document.getElementById('history-preview-container'),
        },
        branchesModal: {
            overlay: document.getElementById('branches-modal'),
            closeButton: document.getElementById('branches-modal-close-button'),
            slotsContainer: document.getElementById('branches-slots-container'),
        },
        branchesConfirmModal: {
            overlay: document.getElementById('branches-confirmation-overlay'),
            message: document.getElementById('branches-confirmation-message'),
            confirmYes: document.getElementById('branches-confirm-yes'),
            confirmNo: document.getElementById('branches-confirm-no'),
        },
        modals: {
            overlay: document.getElementById('custom-modal'),
            message: document.getElementById('modal-message'),
            okButton: document.getElementById('modal-ok-button'),
            confirmButton: document.getElementById('modal-confirm-button'),
            cancelButton: document.getElementById('modal-cancel-button'),
            playersUpgrades: document.getElementById('players-upgrades-modal'),
            playersUpgradesClose: document.getElementById('players-upgrades-modal-close-button'),
            playersUpgradesList: document.getElementById('players-upgrades-list'),
            playersUpgradesFilter: document.getElementById('players-upgrades-filter'),
            playersMissions: document.getElementById('players-missions-modal'),
            playersMissionsClose: document.getElementById('players-missions-modal-close-button'),
            playersMissionsList: document.getElementById('players-missions-list'),
            playersMissionsFilter: document.getElementById('players-missions-filter'),
        },
        historyModal: {
            overlay: document.getElementById('history-modal'),
            closeButton: document.getElementById('history-modal-close-button'),
            playerFilter: document.getElementById('history-player-filter'),
            list: document.getElementById('history-modal-list'),
        },
        missionChoiceModal: {
            overlay: document.getElementById('mission-choice-modal'),
            grid: document.getElementById('mission-choice-grid'),
        },
        payoutModal: {
            overlay: document.getElementById('payout-modal'),
            message: document.getElementById('payout-message'),
            okButton: document.getElementById('payout-ok-button'),
        },
    };

    const socket = io();

    // --- API Functions ---
    const api = {
        checkSession: () => fetch('/api/check_session').then(res => res.json()),
        login: (nickname, faction) => fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nickname, faction }) }).then(handleResponse),
        logout: () => fetch('/api/logout', { method: 'POST' }).then(handleResponse),
        resetGame: () => fetch('/api/reset_game', { method: 'POST' }).then(handleResponse),
        getUserMissions: () => fetch('/api/get_user_missions').then(handleResponse),
        getMissionSelectionData: () => fetch('/api/get_mission_selection_data').then(handleResponse),
        getMissionChoices: (slotIndex, missionClass) => fetch('/api/get_mission_choices', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ slot_index: slotIndex, mission_class: missionClass }) }).then(handleResponse),
        selectMissionChoice: (slotIndex, missionId, isReplacement) => fetch('/api/select_mission_choice', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ slot_index: slotIndex, mission_id: missionId, is_replacement: isReplacement }) }).then(handleResponse),
        updateMissionProgress: (slotId, delta) => fetch('/api/update_mission_progress', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ slot_id: slotId, delta }) }).then(handleResponse),
        completeMission: (slotId) => fetch('/api/complete_mission', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ slot_id: slotId }) }).then(handleResponse),
        getPlayersInfo: () => fetch('/api/get_players_info').then(handleResponse),
        getScoreHistory: () => fetch('/api/get_score_history').then(handleResponse),
        getNews: () => fetch('/api/get_news').then(handleResponse),
        resetNews: () => fetch('/api/reset_news', { method: 'POST' }).then(handleResponse),
        getUpgradesState: () => fetch('/api/get_upgrades_state').then(handleResponse),
        purchaseUpgrade: (upgradeId) => fetch('/api/purchase_upgrade', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ upgrade_id: upgradeId }) }).then(handleResponse),
        rollbackUpgrade: (upgradeId) => fetch('/api/rollback_upgrade', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ upgrade_id: upgradeId }) }).then(handleResponse),
        getAllPlayersUpgrades: () => fetch('/api/get_all_players_upgrades').then(handleResponse),
        getAllPlayersMissions: () => fetch('/api/get_all_players_missions').then(handleResponse),
        getFactions: () => fetch('/api/factions').then(handleResponse),
        getUpgradeOwnership: () => fetch('/api/get_upgrades_ownership').then(handleResponse),
        getGameState: () => fetch('/api/game_state').then(handleResponse),
        setTurnOrder: (order) => fetch('/api/set_turn_order', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ order }) }).then(handleResponse),
        toggleSessionTimer: () => fetch('/api/toggle_session_timer', { method: 'POST' }).then(handleResponse),
        toggleTurnTimer: () => fetch('/api/toggle_turn_timer', { method: 'POST' }).then(handleResponse),
        determineNewInitiative: () => fetch('/api/determine_new_initiative', { method: 'POST' }).then(handleResponse),
        generateNewsForRound: () => fetch('/api/generate_news_for_round', { method: 'POST' }).then(handleResponse),
        nextTurn: () => fetch('/api/next_turn', { method: 'POST' }).then(handleResponse),
        spendActionPoint: (type, amount) => fetch('/api/spend_action_point', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type, amount }) }).then(handleResponse),
    };

    async function handleResponse(response) {
        if (!response.ok) {
            try {
                const errorData = await response.json();
                throw new Error(errorData.error || `Помилка сервера: ${response.status}`);
            } catch (e) {
                throw new Error(`Неочікувана відповідь від сервера: ${response.status}`);
            }
        }
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return await response.json();
        }
        return {};
    }

    function unlockAudio() {
        if (state.audioUnlocked) return;
        console.log("Attempting to unlock mobile audio...");

        const promise1 = state.timerWarningSound.play();
        if (promise1 !== undefined) {
            promise1.then(() => {
                state.timerWarningSound.pause();
                state.timerWarningSound.currentTime = 0;
            }).catch(error => {
                console.error("Audio unlock failed for warning sound:", error);
            });
        }

        const promise2 = state.timerEndSound.play();
        if (promise2 !== undefined) {
            promise2.then(() => {
                state.timerEndSound.pause();
                state.timerEndSound.currentTime = 0;
            }).catch(error => {
                console.error("Audio unlock failed for end sound:", error);
            });
        }
        state.audioUnlocked = true;
    }

    function updateUI() {
        if (!state.gameData) return;
        const {
            nickname, score, level1_score, level2_score, level3_score,
            is_active, faction_color
        } = state.gameData;

        const statusText = is_active ? `${score} Балів` : 'Глядач';
        const coloredNickname = `<span class="player-nickname" style="color: ${faction_color || 'inherit'}">${nickname}</span>`;
        
        DOMElements.mainMenu.userInfo.innerHTML = `/${coloredNickname} : ${statusText}`;
        DOMElements.mission.currentUser.innerHTML = coloredNickname;
        DOMElements.mission.userInfo.innerHTML = is_active ? `Бали: <span>${score}</span>` : 'Статус: Глядач';
        DOMElements.mission.level1Score.textContent = parseFloat(level1_score.toFixed(1));
        DOMElements.mission.level2Score.textContent = parseFloat(level2_score.toFixed(1));
        DOMElements.mission.level3Score.textContent = parseFloat(level3_score.toFixed(1));
    }

    function showScreen(screenName) {
        Object.values(DOMElements.screens).forEach(screen => screen.classList.remove('visible'));
        DOMElements.screens[screenName].classList.add('visible');
        if (screenName === 'login') {
            initLoginScreen();
        }
    }

    function showModal(message, type = 'alert') {
        DOMElements.modals.message.textContent = message;
        DOMElements.modals.okButton.style.display = type === 'alert' ? 'block' : 'none';
        DOMElements.modals.confirmButton.style.display = type === 'confirm' ? 'block' : 'none';
        DOMElements.modals.cancelButton.style.display = type === 'confirm' ? 'block' : 'none';
        DOMElements.modals.overlay.classList.add('visible');
    }
    
    function showConfirm(message, callback) {
        state.confirmCallback = callback;
        showModal(message, 'confirm');
    }

    function hideModal() {
        DOMElements.modals.overlay.classList.remove('visible');
        state.confirmCallback = null;
    }

    function formatTime(totalSeconds, includeHours = false) {
        if (totalSeconds < 0) totalSeconds = 0;
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = Math.floor(totalSeconds % 60);
        const paddedMinutes = String(minutes).padStart(2, '0');
        const paddedSeconds = String(seconds).padStart(2, '0');
        if (includeHours) {
            return `${hours}:${paddedMinutes}:${paddedSeconds}`;
        }
        return `${paddedMinutes}:${paddedSeconds}`;
    }
    
    function renderTimerScreen() {
        const gs = state.gameState;
        if (!gs || !gs.player_turn_timer || !gs.my_action_points) { return; }

        if (state.sessionTimerInterval) clearInterval(state.sessionTimerInterval);
        if (state.playerTimerInterval) clearInterval(state.playerTimerInterval);
        state.timerEndSound.pause();
        state.timerEndSound.currentTime = 0;

        const turnInfoEl = DOMElements.timer.roundInfo.querySelector('span');
        if (gs.is_setup_complete) {
            const totalPlayers = gs.turn_order.length;
            const currentTurnDisplay = gs.is_bot_turn ? "Боти" : gs.turn_order.length > 0 ? `${gs.current_turn_index + 1}/${totalPlayers}` : 'N/A';
            turnInfoEl.textContent = `Новина ${gs.news_round_number}/4 | Раунд ${gs.turn_in_news_round + 1}/4 | Хід: ${currentTurnDisplay}`;
        } else {
            turnInfoEl.textContent = 'Очікування початку гри';
        }

        DOMElements.timer.sessionTimerDisplay.textContent = formatTime(gs.session_timer.elapsed_seconds, true);
        if (gs.session_timer.is_running) {
            startLocalSessionTimer(gs.session_timer.elapsed_seconds);
        }

        const isMyTurn = gs.is_my_turn;
        const turnTimerActive = gs.player_turn_timer.is_active;
        const startButton = DOMElements.timer.startPauseButton;
        const nextPlayerButton = DOMElements.timer.nextPlayerButton;

        DOMElements.timer.actionPointsSection.classList.toggle('hidden', gs.is_bot_turn);

        if (gs.is_bot_turn) {
            DOMElements.timer.playerTurnTitle.textContent = 'Хід ботів';
            DOMElements.timer.botTurnSection.classList.remove('hidden');
            startButton.disabled = true;
            startButton.textContent = "Старт";
            nextPlayerButton.disabled = false;
            nextPlayerButton.textContent = "Завершити раунд";
        } else {
            DOMElements.timer.playerTurnTitle.textContent = `Хід гравця: ${gs.current_player_nickname || 'Очікування'}`;
            DOMElements.timer.botTurnSection.classList.add('hidden');
            const canControlTimer = isMyTurn && gs.player_turn_timer.seconds_left > 0;
            startButton.disabled = !canControlTimer;
            startButton.textContent = turnTimerActive ? "Пауза" : "Старт";
            nextPlayerButton.disabled = !isMyTurn;
            nextPlayerButton.textContent = "Завершити хід";
            const points = isMyTurn ? gs.my_action_points : gs.current_player_action_points;
            if (points) {
                const canUsePoints = isMyTurn && turnTimerActive && gs.player_turn_timer.seconds_left > 0;
                DOMElements.timer.activePointsValue.textContent = `${points.spent_active} / ${points.active}`;
                DOMElements.timer.attackPointsValue.textContent = `${points.spent_attack} / ${points.attack}`;
                DOMElements.timer.buildPointsValue.textContent = `${points.spent_build} / ${points.build}`;
                const minusButtons = DOMElements.timer.actionPointsSection.querySelectorAll('.minus');
                const plusButtons = DOMElements.timer.actionPointsSection.querySelectorAll('.plus');
                minusButtons[0].disabled = !canUsePoints || points.spent_active <= 0;
                plusButtons[0].disabled = !canUsePoints || points.spent_active >= points.active;
                minusButtons[1].disabled = !canUsePoints || points.spent_attack <= 0;
                plusButtons[1].disabled = !canUsePoints || points.spent_attack >= points.attack;
                minusButtons[2].disabled = !canUsePoints || points.spent_build <= 0;
                plusButtons[2].disabled = !canUsePoints || points.spent_build >= points.build;
            }
        }
        const timerValue = formatTime(gs.player_turn_timer.seconds_left);
        DOMElements.timer.playerTimerDisplay.textContent = timerValue;
        Object.values(DOMElements.headerTimers).forEach(timerEl => {
            timerEl.textContent = timerValue;
        });
        if (turnTimerActive) {
            startLocalPlayerTimer(gs.player_turn_timer.seconds_left);
        }
    }
    
    function startLocalSessionTimer(initialSeconds) {
        let elapsed = initialSeconds;
        state.sessionTimerInterval = setInterval(() => {
            elapsed++;
            DOMElements.timer.sessionTimerDisplay.textContent = formatTime(elapsed, true);
        }, 1000);
    }

    function startLocalPlayerTimer(initialSeconds) {
        let remaining = initialSeconds;
        state.warningSoundPlayed = false;
        const updateAllTimers = (time) => {
            const formattedTime = formatTime(time);
            DOMElements.timer.playerTimerDisplay.textContent = formattedTime;
            Object.values(DOMElements.headerTimers).forEach(timerEl => {
                timerEl.textContent = formattedTime;
            });
        };
        updateAllTimers(remaining);
        state.playerTimerInterval = setInterval(() => {
            remaining--;
            updateAllTimers(remaining);
            const isMyTurn = state.gameState && state.gameState.is_my_turn;
            if (remaining <= 10 && remaining > 0) {
                DOMElements.timer.playerTimerDisplay.classList.add('ending');
                if (isMyTurn && !state.warningSoundPlayed) {
                    state.timerWarningSound.play();
                    state.warningSoundPlayed = true;
                }
            } else {
                DOMElements.timer.playerTimerDisplay.classList.remove('ending');
            }
            if (remaining <= 0) {
                clearInterval(state.playerTimerInterval);
                if (isMyTurn) {
                    state.timerEndSound.play();
                }
                document.querySelectorAll('.action-btn').forEach(btn => btn.disabled = true);
            }
        }, 1000);
    }

    function renderMissions() {
        const scrollArea = DOMElements.mission.scrollArea;
        scrollArea.innerHTML = ''; 

        const isMyTurn = state.gameState && state.gameState.is_my_turn;
        const replacements = state.gameData.mission_replacements_by_level || {};

        DOMElements.mission.viewPlayersMissionsButton.disabled = false;
        DOMElements.mission.branchesButton.disabled = isMyTurn;

        for (let level = 1; level <= 3; level++) {
            const levelRow = document.createElement('div');
            levelRow.className = 'mission-level-row';
            
            levelRow.innerHTML = `<h3 class="mission-level-header"><span class="replacement-counter">Замін: ${replacements[level] || 0}</span>Рівень ${level}</h3>`;
            
            const slotsWrapper = document.createElement('div');
            slotsWrapper.className = 'slots-wrapper';

            const leftSlotIndex = level - 1;
            const rightSlotIndex = level - 1 + 3;
            const slotsForLevel = [
                state.missionSlots.find(s => s.slot_index === leftSlotIndex),
                state.missionSlots.find(s => s.slot_index === rightSlotIndex)
            ];

            slotsForLevel.forEach(slot => {
                if (!slot) return;
                let missionItem;
                if (slot.mission_id) {
                    const isCompleted = slot.current_progress >= slot.target_progress;
                    const levelRewardText = `I${'I'.repeat(slot.level - 1)}: ${slot.level_reward_points} Балів`;
                    missionItem = document.createElement('div');
                    missionItem.className = 'mission-item';
                    missionItem.dataset.slotIndex = slot.slot_index; 
                    missionItem.dataset.slotId = slot.id;
                    missionItem.innerHTML = `
                        <div class="mission-header-row">
                            <span class="mission-name">${slot.m_class}: ${slot.name}</span>
                            <button class="mission-action-button replace-mission-btn" title="Замінити місію" ${isMyTurn ? 'disabled' : ''}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
                            </button>
                        </div>
                        <div class="mission-progress-row"><span class="mission-progress-label">Прогрес: ${slot.current_progress}/${slot.target_progress}</span></div>
                        <div class="mission-buttons-row">
                            ${isCompleted ? `<button class="mission-action-button-small execute-btn">Виконати</button>` : `
                                <button class="mission-action-button-small minus-btn">-</button>
                                <button class="mission-action-button-small plus-btn">+</button>
                            `}
                        </div>
                        <div class="mission-rewards-row">
                            <span class="mission-reward-text">${levelRewardText}</span>
                            <span class="mission-reward-text">${slot.main_reward} Балів</span>
                            <span class="mission-reward-text">${slot.currency_reward} валюти</span>
                        </div>`;
                } else {
                    missionItem = document.createElement('div');
                    missionItem.className = 'mission-item mission-item-empty';
                    missionItem.dataset.slotIndex = slot.slot_index;
                    missionItem.dataset.slotId = slot.id;
                    missionItem.innerHTML = `<p>Слот порожній. ${isMyTurn ? 'Завершіть хід, щоб обрати нову місію.' : 'Виберіть місію в "Гілках місій"'}</p>`;
                }
                slotsWrapper.appendChild(missionItem);
            });
            levelRow.appendChild(slotsWrapper);
            scrollArea.appendChild(levelRow);
        }
    }

    function renderBranchesModal() {
        const container = DOMElements.branchesModal.slotsContainer;
        container.innerHTML = '';

        const leftColumn = document.createElement('div');
        leftColumn.className = 'branch-column';

        const rightColumn = document.createElement('div');
        rightColumn.className = 'branch-column';

        const slotMapping = [
            { slotIndex: 0, level: 1, branch: 'Ліва' },
            { slotIndex: 1, level: 2, branch: 'Ліва' },
            { slotIndex: 2, level: 3, branch: 'Ліва' },
            { slotIndex: 3, level: 1, branch: 'Права' },
            { slotIndex: 4, level: 2, branch: 'Права' },
            { slotIndex: 5, level: 3, branch: 'Права' },
        ];

        state.missionSlots.sort((a,b) => a.slot_index - b.slot_index).forEach(slot => {
            const mappedSlot = slotMapping.find(m => m.slotIndex === slot.slot_index);
            if (!mappedSlot) return;

            const slotEl = document.createElement('div');
            slotEl.className = 'branch-slot-card';
            slotEl.dataset.slotIndex = slot.slot_index;

            let missionName = slot.mission_id ? slot.m_class : 'Слот порожній';

            slotEl.innerHTML = `
                <div class="branch-slot-header">
                    <h4>${mappedSlot.branch} Гілка - Рівень ${mappedSlot.level}</h4>
                    <span>${missionName}</span>
                </div>
                <div class="branch-slot-controls">
                    <button class="class-button" data-class="Атака">Атака</button>
                    <button class="class-button" data-class="Захист">Захист</button>
                    <button class="class-button" data-class="Лут">Лут</button>
                    <button class="class-button" data-class="Економіка">Економіка</button>
                </div>
            `;
            
            const buttons = slotEl.querySelectorAll('.class-button');
            buttons.forEach(button => {
                const missionClass = button.dataset.class;
                const unlockedTier = state.unlockedTiers[missionClass] || 1;
                const slotLevel = mappedSlot.level;

                if (slotLevel <= unlockedTier) {
                    button.classList.add('available');
                } else {
                    button.classList.add('unavailable');
                }
            });
            
            if (mappedSlot.branch === 'Ліва') {
                leftColumn.appendChild(slotEl);
            } else {
                rightColumn.appendChild(slotEl);
            }
        });

        container.appendChild(leftColumn);
        container.appendChild(rightColumn);
    }

    function renderNews(newsData) {
        const { round_number, news } = newsData;
        DOMElements.news.roundIndicator.textContent = `Новина ${round_number}`;
        const scrollArea = DOMElements.news.scrollArea;
        scrollArea.innerHTML = '';

        if (news && news.length > 0) {
            news.forEach(item => {
                const newsEl = document.createElement('div');
                newsEl.className = 'news-item';
                newsEl.textContent = item;
                scrollArea.appendChild(newsEl);
            });
        } else {
            scrollArea.innerHTML = '<p class="news-item">Новин ще немає.</p>';
        }
        
        const nextNewsButton = document.getElementById('next-news-button');
        if(nextNewsButton) nextNewsButton.style.display = 'none';

        if (round_number >= 4) {
            DOMElements.news.resetButton.style.display = 'block';
        } else {
            DOMElements.news.resetButton.style.display = 'none';
        }
    }

    function renderMissionChoiceModal(choices, slotIndex, isReplacement) {
        const grid = DOMElements.missionChoiceModal.grid;
        grid.innerHTML = '';
        state.missionChoiceContext = { slotIndex, isReplacement };

        if (!choices || choices.length === 0) {
            grid.innerHTML = '<p>Немає доступних місій.</p>';
            DOMElements.missionChoiceModal.overlay.classList.add('visible');
            return;
        }

        choices.forEach(mission => {
            const card = document.createElement('div');
            card.className = 'mission-choice-card';
            card.dataset.missionId = mission.id;
            card.innerHTML = `
                <div class="mission-choice-name">${mission.name}</div>
                <div class="mission-choice-description">${mission.description}</div>
                <div class="mission-choice-rewards">
                    <span>${'I'.repeat(mission.level)}: ${mission.level_reward_points}</span>
                    <span>${mission.main_reward} Балів</span>
                    <span>${mission.currency_reward} валюти</span>
                </div>
            `;
            grid.appendChild(card);
        });

        DOMElements.missionChoiceModal.overlay.classList.add('visible');
    }

    async function handleMissionChoiceClick(event) {
        const card = event.target.closest('.mission-choice-card');
        if (!card || !state.missionChoiceContext) return;

        const missionId = parseInt(card.dataset.missionId, 10);
        const { slotIndex, isReplacement } = state.missionChoiceContext;

        try {
            await api.selectMissionChoice(slotIndex, missionId, isReplacement);
            DOMElements.missionChoiceModal.overlay.classList.remove('visible');
            DOMElements.branchesModal.overlay.classList.remove('visible'); // <-- ДОДАЙТЕ ЦЕЙ РЯДОК
            await refreshCurrentPlayerAndMissions();
        } catch (error) {
            showModal(error.message);
        } finally {
            state.missionChoiceContext = null;
        }
    }

    async function openMissionChoices(slotIndex, missionClass) {
        const slot = state.missionSlots.find(s => s.slot_index === slotIndex);
        if (!slot) return;
        
        const isReplacement = !!slot.mission_id;
        const message = isReplacement 
            ? `Замінити місію? Це використає 1 очко заміни.`
            : `Взяти нову місію класу "${missionClass}"?`;
        
        showConfirm(message, async () => {
            try {
                const choices = await api.getMissionChoices(slotIndex, missionClass);
                renderMissionChoiceModal(choices, slotIndex, isReplacement);
            } catch (error) {
                if (error.message && error.message.includes("Закінчилися заміни")) {
                    const customMessage = "Заміни на цьому рівні закінчились, без них можна обрати місії в пустий слот або чекати кінця твого наступного ходу, тоді заміна відновиться";
                    showModal(customMessage);
                } else {
                    showModal(error.message);
                }
            }
        });
    }

    async function handleMissionChoiceClick(event) {
        const card = event.target.closest('.mission-choice-card');
        if (!card || !state.missionChoiceContext) return;

        const missionId = parseInt(card.dataset.missionId, 10);
        const { slotIndex, isReplacement } = state.missionChoiceContext;

        try {
            await api.selectMissionChoice(slotIndex, missionId, isReplacement);
            DOMElements.missionChoiceModal.overlay.classList.remove('visible');
            DOMElements.branchesModal.overlay.classList.remove('visible');
            await refreshCurrentPlayerAndMissions();
        } catch (error) {
            showModal(error.message);
        } finally {
            state.missionChoiceContext = null;
        }
    }

    async function openMissionChoices(slotIndex, missionClass) {
        const slot = state.missionSlots.find(s => s.slot_index === slotIndex);
        if (!slot) return;
        
        const isReplacement = !!slot.mission_id;
        const message = isReplacement 
            ? `Замінити місію? Це використає 1 очко заміни.`
            : `Взяти нову місію класу "${missionClass}"?`;
        
        showConfirm(message, async () => {
            try {
                const choices = await api.getMissionChoices(slotIndex, missionClass);
                renderMissionChoiceModal(choices, slotIndex, isReplacement);
            } catch (error) {
                if (error.message && error.message.includes("Закінчилися заміни")) {
                    const customMessage = "Заміни на цьому рівні закінчились, без них можна обрати місії в пустий слот або чекати кінця твого наступного ходу, тоді заміна відновиться";
                    showModal(customMessage);
                } else {
                    showModal(error.message);
                }
            }
        });
    }

    function renderUpgradeTree() {
        const container = DOMElements.upgrades.treeContainer;
        container.innerHTML = '';
        DOMElements.upgrades.pointsDisplay.innerHTML = `
            <span class="mission-stat">I: <span id="upgrades-stat-i">${parseFloat(state.gameData.level1_score.toFixed(1))}</span></span>
            <span class="mission-stat">II: <span id="upgrades-stat-ii">${parseFloat(state.gameData.level2_score.toFixed(1))}</span></span>
            <span class="mission-stat">III: <span id="upgrades-stat-iii">${parseFloat(state.gameData.level3_score.toFixed(1))}</span></span>
        `;
        
        const purchasedByTier = { 1: 0, 2: 0, 3: 0 };
        state.upgrades.purchased.forEach(pId => {
            const tier = state.upgrades.tree[pId]?.tier;
            if (tier) purchasedByTier[tier]++;
        });

        DOMElements.upgrades.limitsDisplay.innerHTML = `
            <span class="limit-stat">1р: ${purchasedByTier[1]}/4</span>
            <span class="limit-stat">2р: ${purchasedByTier[2]}/3</span>
            <span class="limit-stat">3р: ${purchasedByTier[3]}/2</span>
        `;

        const categories = ["Захист", "Атака", "Лут", "Економіка", "Командування"];
        const upgradesByCategory = {};
        Object.values(state.upgrades.tree).forEach(upg => {
            if (!upgradesByCategory[upg.category]) upgradesByCategory[upg.category] = [];
            upgradesByCategory[upg.category].push(upg);
        });

        categories.forEach(category => {
            const branchEl = document.createElement('div');
            branchEl.className = 'upgrade-branch';
            
            const titleEl = document.createElement('h3');
            titleEl.className = 'branch-title';
            titleEl.textContent = category;
            branchEl.appendChild(titleEl);

            const tierWrapper = document.createElement('div');
            tierWrapper.className = 'tier-wrapper';

            const tiers = { 1: [], 2: [], 3: [] };
            (upgradesByCategory[category] || []).forEach(upg => tiers[upg.tier].push(upg));

            for (let tier = 1; tier <= 3; tier++) {
                const tierEl = document.createElement('div');
                tierEl.className = 'upgrade-tier';
                tiers[tier].forEach(upgrade => {
                    const nodeEl = document.createElement('div');
                    nodeEl.className = 'upgrade-node';
                    nodeEl.dataset.upgradeId = upgrade.id;
                    const isPurchased = state.upgrades.purchased.includes(upgrade.id);
                    let isAvailable = false;
                    if (!isPurchased) {
                        const tierLimit = {1: 4, 2: 3, 3: 2}[tier];
                        const isBranchOccupied = state.upgrades.purchased.some(pId => state.upgrades.tree[pId]?.category === category && state.upgrades.tree[pId]?.tier === tier);
                        if (purchasedByTier[tier] < tierLimit && !isBranchOccupied) {
                            if (upgrade.category === "Командування") {
                                const hasOtherTierUpgrade = state.upgrades.purchased.some(pId => state.upgrades.tree[pId]?.tier === tier && state.upgrades.tree[pId]?.category !== "Командування");
                                isAvailable = state.upgrades.round_number >= tier && hasOtherTierUpgrade;
                            } else {
                                const userPoints = state.gameData[`level${tier}_score`];
                                if (tier === 1) {
                                    isAvailable = userPoints >= upgrade.cost;
                                } else {
                                    const hasPrerequisite = state.upgrades.purchased.some(pId => state.upgrades.tree[pId]?.category === category && state.upgrades.tree[pId]?.tier === tier - 1);
                                    isAvailable = hasPrerequisite && userPoints >= upgrade.cost;
                                }
                            }
                        }
                    }
                    if (isPurchased) nodeEl.classList.add('purchased');
                    else if (isAvailable) nodeEl.classList.add('available');
                    else nodeEl.classList.add('locked');
                    const costText = upgrade.category === "Командування" ? "Безкоштовно" : `Вартість: ${upgrade.cost} <strong>${'I'.repeat(tier)}</strong>`;
                    nodeEl.innerHTML = `
                        <div class="upgrade-ownership-indicators"></div>
                        <p class="upgrade-name">${upgrade.name}</p>
                        <p class="upgrade-cost">${costText}</p>
                        ${isPurchased ? '<button class="rollback-btn" title="Відкат прокачки">&times;</button>' : ''}
                    `;
                    tierEl.appendChild(nodeEl);
                });
                tierWrapper.appendChild(tierEl);
                if (tier < 3) {
                    const connector = document.createElement('div');
                    connector.className = 'connector';
                    tierWrapper.appendChild(connector);
                }
            }
            branchEl.appendChild(tierWrapper);
            container.appendChild(branchEl);
        });
        renderUpgradeIndicators();
    }
    
    function renderUpgradeIndicators() {
        const ownership = state.upgradeOwnership;
        if (!ownership) return;
        document.querySelectorAll('.upgrade-ownership-indicators').forEach(el => el.innerHTML = '');
        for (const upgradeId in ownership) {
            const owners = ownership[upgradeId];
            const node = DOMElements.upgrades.treeContainer.querySelector(`[data-upgrade-id="${upgradeId}"]`);
            if (node) {
                const indicatorContainer = node.querySelector('.upgrade-ownership-indicators');
                if (indicatorContainer) {
                    owners.forEach(owner => {
                        if (owner.nickname === state.gameData.nickname) return;
                        const indicator = document.createElement('div');
                        indicator.className = 'ownership-indicator';
                        indicator.style.backgroundColor = owner.faction_color;
                        indicator.title = owner.nickname;
                        indicatorContainer.appendChild(indicator);
                    });
                }
            }
        }
    }

    async function fetchAndRenderUpgrades() {
        try {
            const [upgradeData, ownershipData] = await Promise.all([
                api.getUpgradesState(),
                api.getUpgradeOwnership()
            ]);
            state.upgrades = upgradeData;
            state.upgradeOwnership = ownershipData;
            renderUpgradeTree();
        } catch (error) {
            console.error("Failed to fetch upgrades:", error);
            DOMElements.upgrades.treeContainer.innerHTML = '<p>Не вдалося завантажити прокачки.</p>';
        }
    }

    async function fetchAndRenderNews() {
        try {
            const newsData = await api.getNews();
            renderNews(newsData);
        } catch (error) {
            console.error("Failed to fetch news:", error);
            DOMElements.news.scrollArea.innerHTML = '<p class="news-item">Не вдалося завантажити новини.</p>';
        }
    }

    async function renderTopPlayers() {
        const list = DOMElements.score.topPlayersList;
        list.innerHTML = 'Завантаження...';
        try {
            const players = await api.getPlayersInfo();
            list.innerHTML = '';
            if (!players || players.length === 0) {
                list.innerHTML = '<p class="player-score-item">Наразі немає гравців.</p>';
                return;
            }
            players.forEach(player => {
                const youLabel = state.gameData && player.nickname === state.gameData.nickname ? '<span class="you-label"> (Ви)</span>' : '';
                const levelScores = `<span class="level-scores">I: ${parseFloat(player.level1_score.toFixed(1))} II: ${parseFloat(player.level2_score.toFixed(1))} III: ${parseFloat(player.level3_score.toFixed(1))}</span>`;
                const coloredNickname = `<span class="player-nickname" style="color: ${player.faction_color || 'inherit'}">${player.nickname}</span>`;
                list.innerHTML += `<div class="player-score-item"><div class="player-info">${coloredNickname}${youLabel}${levelScores}</div><span class="main-score">${player.score} Балів</span></div>`;
            });
        } catch (error) {
            console.error('Помилка при отриманні топ гравців:', error);
            list.innerHTML = '<p class="player-score-item">Не вдалося завантажити топ гравців.</p>';
        }
    }

    function renderScoreHistory(history, container, limit = 0) {
        container.innerHTML = '';
        const itemsToRender = limit > 0 ? history.slice(0, limit) : history;
        if (!history || history.length === 0) {
            container.innerHTML = '<p class="history-item">Історія порожня.</p>';
            return;
        }
        itemsToRender.forEach(item => {
            const romanLevel = 'I'.repeat(item.level);
            let reward = `+${item.score_change} балів | +${item.level_score_change} балів ${romanLevel}`;
            if (item.currency_change > 0) {
                reward += ` | +${item.currency_change} валюти`;
            }
            const coloredNickname = `<span class="nickname" style="color: ${item.faction_color || 'inherit'}">${item.nickname}</span>`;
            container.innerHTML += `
                <div class="history-item">
                    <div class="history-item-info">
                        ${coloredNickname}
                        <span class="reason">${item.reason}</span>
                    </div>
                    <div class="history-item-reward">
                        <span class="score-change">${reward}</span>
                    </div>
                </div>
            `;
        });
    }

    function renderFilteredPlayerUpgrades() {
        const selectedNickname = DOMElements.modals.playersUpgradesFilter.value;
        const list = DOMElements.modals.playersUpgradesList;
        list.innerHTML = '';
        const playersToRender = selectedNickname === 'all'
            ? Object.keys(state.allPlayerUpgrades)
            : [selectedNickname];

        if (playersToRender.length === 0) {
            list.innerHTML = '<p>Немає даних для відображення.</p>';
            return;
        }
        playersToRender.forEach(nickname => {
            const playerData = state.allPlayerUpgrades[nickname];
            const upgrades = playerData.upgrades;
            const playerEl = document.createElement('div');
            playerEl.className = 'player-upgrades-item';
            let upgradesHTML = '<ul>';
            if (upgrades && upgrades.length > 0) {
                upgrades.forEach(upg => {
                    upgradesHTML += `<li><strong>${upg.category} / Рівень ${upg.tier}:</strong> ${upg.name}</li>`;
                });
            } else {
                upgradesHTML += '<li>Немає прокачок</li>';
            }
            upgradesHTML += '</ul>';
            const coloredNickname = `<h4 style="color: ${playerData.faction_color || 'inherit'}">${nickname}</h4>`;
            playerEl.innerHTML = `${coloredNickname}${upgradesHTML}`;
            list.appendChild(playerEl);
        });
    }

    async function fetchAndRenderPlayerUpgrades() {
        try {
            const allUpgrades = await api.getAllPlayersUpgrades();
            state.allPlayerUpgrades = allUpgrades;
            const filter = DOMElements.modals.playersUpgradesFilter;
            const currentVal = filter.value;
            filter.innerHTML = '<option value="all">Всі гравці</option>';
            Object.keys(allUpgrades).forEach(nickname => {
                const option = document.createElement('option');
                option.value = nickname;
                option.textContent = nickname;
                filter.appendChild(option);
            });
            filter.value = currentVal;
            renderFilteredPlayerUpgrades();
            DOMElements.modals.playersUpgrades.classList.add('visible');
        } catch (error) {
            DOMElements.modals.playersUpgradesList.innerHTML = '<p>Не вдалося завантажити дані.</p>';
            console.error(error);
        }
    }

    function renderFilteredPlayerMissions() {
        const selectedNickname = DOMElements.modals.playersMissionsFilter.value;
        const list = DOMElements.modals.playersMissionsList;
        list.innerHTML = '';
        const playersToRender = selectedNickname === 'all'
            ? Object.keys(state.allPlayerMissions)
            : [selectedNickname];

        if (playersToRender.length === 0) {
            list.innerHTML = '<p>Немає даних для відображення.</p>';
            return;
        }
        playersToRender.forEach(nickname => {
            const playerData = state.allPlayerMissions[nickname];
            const missions = playerData.missions;
            const playerEl = document.createElement('div');
            playerEl.className = 'player-missions-item';
            let missionsHTML = '';
            const activeMissions = missions.filter(m => m.mission_id);
            if (activeMissions.length > 0) {
                missionsHTML += '<div class="player-missions-grid">';
                activeMissions.forEach(m => {
                    missionsHTML += `
                        <div class="player-mission-card">
                            <div class="player-mission-title">${m.name}</div>
                            <div class="player-mission-class">${m.m_class} - Рівень ${m.level}</div>
                            <div class="player-mission-progress">Прогрес: ${m.current_progress}/${m.target_progress}</div>
                        </div>
                    `;
                });
                missionsHTML += '</div>';
            } else {
                missionsHTML = '<p>Активних місій немає</p>';
            }
            const coloredNickname = `<h4 style="color: ${playerData.faction_color || 'inherit'}">${nickname}</h4>`;
            playerEl.innerHTML = `${coloredNickname}${missionsHTML}`;
            list.appendChild(playerEl);
        });
    }

    async function fetchAndRenderPlayerMissions() {
        try {
            const allMissions = await api.getAllPlayersMissions();
            state.allPlayerMissions = allMissions;
            const filter = DOMElements.modals.playersMissionsFilter;
            const currentVal = filter.value;
            filter.innerHTML = '<option value="all">Всі гравці</option>';
            Object.keys(allMissions).forEach(nickname => {
                const option = document.createElement('option');
                option.value = nickname;
                option.textContent = nickname;
                filter.appendChild(option);
            });
            filter.value = currentVal;
            renderFilteredPlayerMissions();
            DOMElements.modals.playersMissions.classList.add('visible');
        } catch (error) {
            DOMElements.modals.playersMissionsList.innerHTML = '<p>Не вдалося завантажити дані.</p>';
            console.error(error);
        }
    }

    async function handleLogin() {
        unlockAudio();
        const nickname = DOMElements.login.nicknameInput.value.trim();
        const faction = DOMElements.login.factionSelect.value;
        if (!nickname) {
            DOMElements.login.loginMessage.textContent = 'Будь ласка, введіть ваш нікнейм.';
            return;
        }
        if (!faction) {
            DOMElements.login.loginMessage.textContent = 'Будь ласка, виберіть угрупування.';
            return;
        }
        DOMElements.login.loginMessage.textContent = '';
        try {
            const userData = await api.login(nickname, faction);
            sessionStorage.setItem('kpk_nickname', nickname);
            state.gameData = userData;
            updateUI();
            showScreen('mainMenu');
            await fetchAndRenderGameState();
        } catch (error) {
            DOMElements.login.loginMessage.textContent = error.message;
        }
    }
    
    function handleLogout() {
        showConfirm("Ви впевнені, що хочете вийти?", async () => {
            try {
                await api.logout();
                sessionStorage.removeItem('kpk_nickname');
                state.gameData = null;
                window.location.reload();
            } catch (error) {
                showModal(`Помилка виходу: ${error.message}`);
            }
        });
    }

    function handleResetGame() {
        showConfirm("Ви впевнені, що хочете повністю скинути гру? УСІ дані будуть видалені.", async () => {
            try {
                const result = await api.resetGame();
                showModal(result.message);
                sessionStorage.removeItem('kpk_nickname');
                state.gameData = null;
                 setTimeout(() => window.location.reload(), 1500);
            } catch (error) {
                showModal(`Помилка скидання: ${error.message}`);
            }
        });
    }

    async function handleMissionClick(event) {
        const target = event.target;
        const missionItem = target.closest('.mission-item');
        if (!missionItem) return;

        if (target.disabled) {
            if (state.gameState && state.gameState.is_my_turn) {
                showModal("Заміняти місії можна лише поза своїм ходом.");
            } else {
                showModal("Виконувати місії можна лише у свій хід.");
            }
            return;
        }

        if (missionItem.classList.contains('mission-item-empty')) {
            showModal("Цей слот порожній. Виберіть місію в 'Гілках місій'.");
            return;
        }

        const slotIndex = parseInt(missionItem.dataset.slotIndex, 10);
        const slot = state.missionSlots.find(s => s.slot_index === slotIndex);
        if (!slot || !slot.mission_id) {
            showModal("Не вдалося знайти місію для цього слота або слот порожній.");
            return;
        }

        const slotId = slot.id;
        
        async function performActionAndUpdate(actionPromise) {
            try {
                const result = await actionPromise;
                if (result && result.message) {
                    const isMyTurn = state.gameState && state.gameState.is_my_turn;
                    if (!isMyTurn && result.currency_reward > 0) {
                        showModal(`${result.message} | +${result.currency_reward} валюти`);
                    } else {
                        showModal(result.message);
                    }
                }
                await refreshCurrentPlayerAndMissions();
            } catch (error) {
                if (error.message && error.message.includes("закінчилися очки заміни")) {
                    showModal("У вас закінчилися очки заміни місій.");
                } else {
                    showModal(error.message);
                }
            }
        }
        
        if (target.closest('.replace-mission-btn')) {
            await openMissionChoices(slot.slot_index, slot.m_class);
            return;
        }

        if (target.matches('.plus-btn, .minus-btn')) {
            performActionAndUpdate(api.updateMissionProgress(slotId, target.matches('.plus-btn') ? 1 : -1));
        } else if (target.matches('.execute-btn')) {
            performActionAndUpdate(api.completeMission(slotId));
        }
    }

    async function handleBranchesModalOpen() {
        if (state.gameState && state.gameState.is_my_turn) {
            showModal("Обирати та заміняти місії можна лише поза своїм ходом.");
            return;
        }
        try {
            const selectionData = await api.getMissionSelectionData();
            state.unlockedTiers = selectionData.unlocked_tiers;
            renderBranchesModal();
            DOMElements.branchesModal.overlay.classList.add('visible');
        }
        catch (error) {
            showModal(error.message);
        }
    }

    function showBranchesConfirm(message, callback) {
        DOMElements.branchesConfirmModal.message.textContent = message;
        state.branchesConfirmCallback = callback;
        DOMElements.branchesConfirmModal.overlay.classList.add('visible');
    }

    function hideBranchesConfirm() {
        DOMElements.branchesConfirmModal.overlay.classList.remove('visible');
        state.branchesConfirmCallback = null;
    }

    async function handleClassButtonClick(event) {
        if (!event.target.classList.contains('class-button')) return;

        // Одразу ховаємо вікно "Гілок місій"
        DOMElements.branchesModal.overlay.classList.remove('visible');

        const card = event.target.closest('.branch-slot-card');
        const slotIndex = parseInt(card.dataset.slotIndex, 10);
        const missionClass = event.target.dataset.class;
        
        // А вже після цього викликаємо вікно підтвердження
        await openMissionChoices(slotIndex, missionClass);
    }

    async function handleUpgradeTreeClick(event) {
        if (state.gameState && !state.gameState.is_my_turn) {
            showModal("Купувати прокачки можна лише у свій хід.");
            return;
        }
        const availableNode = event.target.closest('.upgrade-node.available');
        const rollbackButton = event.target.closest('.rollback-btn');
        if (availableNode) {
            const upgradeId = availableNode.dataset.upgradeId;
            const upgrade = state.upgrades.tree[upgradeId];
            if (!upgrade) return;
            const costText = upgrade.category === "Командування" ? "Безкоштовно" : `за ${upgrade.cost} бал(и) ${'I'.repeat(upgrade.tier)} рівня`;
            showConfirm(`Купити прокачку "${upgrade.name}" ${costText}?`, async () => {
                try {
                    await api.purchaseUpgrade(upgradeId);
                    await refreshDataForUpgrades();
                } catch (error) {
                    showModal(error.message);
                }
            });
        } else if (rollbackButton) {
            const purchasedNode = rollbackButton.closest('.upgrade-node.purchased');
            const upgradeId = purchasedNode.dataset.upgradeId;
            if (!upgradeId) return;
            showConfirm(`Відкотити цю прокачку та всі залежні від неї? Бали будуть повернуті.`, async () => {
                try {
                    await api.rollbackUpgrade(upgradeId);
                    await refreshDataForUpgrades();
                } catch (error) {
                    showModal(error.message);
                }
            });
        }
    }

    async function fetchAndRenderScoreScreen() {
        renderTopPlayers();
        try {
            state.scoreHistory = await api.getScoreHistory();
            renderScoreHistory(state.scoreHistory, DOMElements.score.historyPreviewContainer, 5);
        } catch (error) {
            console.error("Failed to load score history", error);
        }
    }
    
    async function fetchAndRenderMissions() {
        try {
            state.missionSlots = await api.getUserMissions();
            renderMissions();
        } catch (error) {
            DOMElements.mission.scrollArea.innerHTML = '<p>Не вдалося завантажити місії.</p>';
        }
    }

    async function openHistoryModal() {
        DOMElements.historyModal.overlay.classList.add('visible');
        try {
            const players = await api.getPlayersInfo();
            const filterSelect = DOMElements.historyModal.playerFilter;
            filterSelect.innerHTML = '<option value="all">Всі гравці</option>';
            players.forEach(player => {
                const option = document.createElement('option');
                option.value = player.nickname;
                option.textContent = player.nickname;
                filterSelect.appendChild(option);
            });
            filterHistory();
        } catch (error) {
            console.error("Failed to load players for history filter:", error);
        }
    }

    function filterHistory() {
        const selectedNickname = DOMElements.historyModal.playerFilter.value;
        const filteredHistory = selectedNickname === 'all'
            ? state.scoreHistory
            : state.scoreHistory.filter(item => item.nickname === selectedNickname);
        renderScoreHistory(filteredHistory, DOMElements.historyModal.list);
    }
    
    async function refreshDataForUpgrades() {
        const sessionData = await api.checkSession();
        if (sessionData.logged_in) {
            state.gameData = sessionData.user;
            updateUI();
            await fetchAndRenderUpgrades();
        }
    }
    
    async function refreshCurrentPlayerAndMissions() {
        if (!sessionStorage.getItem('kpk_nickname')) return;
        try {
            const sessionData = await api.checkSession();
            if (sessionData.logged_in) {
                state.gameData = sessionData.user;
                updateUI();
                await fetchAndRenderMissions();
            } else {
                sessionStorage.removeItem('kpk_nickname');
                window.location.reload();
            }
        } catch (error) {
            console.error("Could not refresh player data:", error);
        }
    }

    async function initLoginScreen() {
        try {
            const factionData = await api.getFactions();
            state.factionData = factionData;
            populateFactionSelector();
        } catch (error) {
            console.error("Сервер не віддав список угруповань. Використовується запасний варіант:", error);
            DOMElements.login.loginMessage.textContent = "Показано всі угрупування. Сервер перевірить вибір при вході.";
            const fallbackFactions = {
                'Скаєри': '#66ADFF', 'Авантюристи': '#A0A0A0', 'Військові': '#FF8282',
                'Цикади': '#A9FFAF', 'Глодекс': '#F9FF9E', 'Розсвіт': '#7EF2FF'
            };
            state.factionData = { factions: fallbackFactions, taken: [] };
            populateFactionSelector();
        }
    }

    function populateFactionSelector() {
        const select = DOMElements.login.factionSelect;
        select.innerHTML = '';
        const placeholder = document.createElement('option');
        placeholder.value = "";
        placeholder.textContent = "Виберіть угрупування";
        placeholder.disabled = true;
        placeholder.selected = true;
        select.appendChild(placeholder);
        const randomOption = document.createElement('option');
        randomOption.value = "random";
        randomOption.textContent = "Випадковий вибір";
        select.appendChild(randomOption);
        const { factions, taken } = state.factionData;
        for (const name in factions) {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            option.style.color = factions[name];
            if (taken.includes(name)) {
                option.disabled = true;
                option.textContent += " (Зайнято)";
            }
            select.appendChild(option);
        }
    }

    async function handleToggleTurnTimerClick() {
        try {
            await api.toggleTurnTimer();
        } catch (error) {
            showModal(error.message);
        }
    }

    async function handleNextPlayerClick() {
        if (state.gameState.is_bot_turn) {
            showConfirm("Ви впевнені, що хочете завершити раунд?", async () => {
                try {
                    await api.nextTurn();
                } catch (error) {
                    showModal(error.message);
                }
            });
            return;
        }
        const currencyToPay = state.gameData.currency_earned_this_turn;
        const confirmAndEndTurn = () => {
            showConfirm("Ви впевнені, що хочете завершити хід?", async () => {
                try {
                    await api.nextTurn();
                } catch (error) {
                    showModal(error.message);
                }
            });
        };
        if (currencyToPay > 0) {
            DOMElements.payoutModal.message.textContent = `До виплати за місії: ${currencyToPay} валюти`;
            DOMElements.payoutModal.overlay.classList.add('visible');
            DOMElements.payoutModal.okButton.onclick = () => {
                DOMElements.payoutModal.overlay.classList.remove('visible');
                confirmAndEndTurn();
            };
        } else {
            confirmAndEndTurn();
        }
    }

    async function handleSessionTimerClick() {
        try {
            await api.toggleSessionTimer();
        } catch (error) {
            showModal(error.message);
        }
    }

    async function handleActionPointClick(event) {
        const button = event.target.closest('.action-btn');
        if (!button || button.disabled) return;
        const type = button.dataset.type;
        const amount = button.classList.contains('plus') ? 1 : -1;
        try {
            await api.spendActionPoint(type, amount);
        } catch (error) {
            showModal(error.message);
        }
    }

    async function handleNewsScreenOpen() {
        showScreen('news');
        await fetchAndRenderGameState(); 
        if (!state.gameState) return;
        const gs = state.gameState;
        DOMElements.news.initiativeSetupView.classList.add('hidden');
        DOMElements.news.determineInitiativeView.classList.add('hidden');
        DOMElements.news.initiativeResultView.classList.add('hidden');
        DOMElements.news.newsContentWrapper.classList.add('hidden');
        const initiativeScreen = DOMElements.news.initiativeScreen;
        initiativeScreen.classList.remove('hidden');
        if (gs.is_game_over) {
            initiativeScreen.classList.remove('hidden');
            DOMElements.news.determineInitiativeView.classList.remove('hidden');
            DOMElements.news.determineInitiativeTitle.textContent = "Гру завершено!";
            DOMElements.news.determineInitiativeView.querySelector('p').style.display = 'none';
            DOMElements.news.determineInitiativeButton.style.display = 'none';
        } else if (gs.needs_new_initiative) {
            initiativeScreen.classList.remove('hidden');
            DOMElements.news.determineInitiativeView.classList.remove('hidden');
            DOMElements.news.determineInitiativeTitle.textContent = "Раунд завершено";
            DOMElements.news.determineInitiativeView.querySelector('p').style.display = 'block';
            DOMElements.news.determineInitiativeButton.style.display = 'block';
        } else if (!gs.is_setup_complete) {
            initiativeScreen.classList.remove('hidden');
            DOMElements.news.initiativeSetupView.classList.remove('hidden');
            const players = await api.getPlayersInfo();
            const selectionContainer = DOMElements.news.initiativePlayerOrderSelection;
            selectionContainer.innerHTML = '';
            players.forEach(player => {
                const playerEl = document.createElement('div');
                playerEl.className = 'initiative-player-item';
                playerEl.textContent = player.nickname;
                playerEl.dataset.nickname = player.nickname;
                playerEl.draggable = true;
                selectionContainer.appendChild(playerEl);
            });
            if (typeof Sortable !== 'undefined') {
                new Sortable(selectionContainer, { animation: 150 });
            }
        } else {
            initiativeScreen.classList.add('hidden');
            DOMElements.news.newsContentWrapper.classList.remove('hidden');
            fetchAndRenderNews();
        }
    }
    
    async function handleInitiativeConfirm() {
        const playerItems = DOMElements.news.initiativePlayerOrderSelection.querySelectorAll('.initiative-player-item');
        const order = Array.from(playerItems).map(item => item.dataset.nickname);
        try {
            await api.setTurnOrder(order);
        } catch (error) {
            showModal(error.message);
        }
    }

    async function handleDetermineInitiativeClick() {
        try {
            const result = await api.determineNewInitiative();
            showModal(`Ініціатива у гравця: ${result.new_initiative_player}`);
        } catch (error) {
            showModal(error.message);
        }
    }

    async function handleNextNewsClick() {
        try {
            await api.nextNews();
        } catch (error) {
            showModal(error.message);
        }
    }

    async function fetchAndRenderGameState() {
        try {
            state.gameState = await api.getGameState();
            renderTimerScreen();
        } catch (error) {
            console.error("Failed to fetch game state:", error);
        }
    }
    
async function initialize() {
        // --- Обробники подій для екрану входу та головного меню ---
        DOMElements.login.loginButton.addEventListener('click', handleLogin);
        DOMElements.login.nicknameInput.addEventListener('keyup', (e) => e.key === 'Enter' && handleLogin());
        DOMElements.mainMenu.logoutButton.addEventListener('click', handleLogout);
        DOMElements.mainMenu.resetButton.addEventListener('click', handleResetGame);
        
        DOMElements.mainMenu.missionButton.addEventListener('click', () => {
            fetchAndRenderMissions();
            showScreen('mission');
        });
        DOMElements.mainMenu.yebalyButton.addEventListener('click', () => {
            fetchAndRenderScoreScreen();
            showScreen('score');
        });
        DOMElements.mainMenu.newsButton.addEventListener('click', handleNewsScreenOpen);
        DOMElements.mainMenu.upgradesButton.addEventListener('click', () => {
            fetchAndRenderUpgrades();
            showScreen('upgrades');
        });
        
        // --- Обробники подій для екранів та їх модальних вікон ---
        
        // Місії
        DOMElements.mission.scrollArea.addEventListener('click', handleMissionClick);
        DOMElements.mission.backButton.addEventListener('click', () => showScreen('mainMenu'));
        DOMElements.mission.branchesButton.addEventListener('click', handleBranchesModalOpen);
        DOMElements.mission.viewPlayersMissionsButton.addEventListener('click', fetchAndRenderPlayerMissions);
        DOMElements.missionChoiceModal.grid.addEventListener('click', handleMissionChoiceClick);
        DOMElements.branchesModal.closeButton.addEventListener('click', () => DOMElements.branchesModal.overlay.classList.remove('visible'));
        DOMElements.branchesModal.slotsContainer.addEventListener('click', handleClassButtonClick);
        DOMElements.branchesConfirmModal.confirmNo.addEventListener('click', hideBranchesConfirm);
        DOMElements.branchesConfirmModal.confirmYes.addEventListener('click', () => {
            if (state.branchesConfirmCallback) state.branchesConfirmCallback();
            hideBranchesConfirm();
        });

        // ЄБали (Рахунок)
        DOMElements.score.backButton.addEventListener('click', () => showScreen('mainMenu'));
        DOMElements.score.historyPreviewContainer.addEventListener('click', openHistoryModal);
        
        // Новини
        DOMElements.news.backButton.addEventListener('click', () => showScreen('mainMenu'));
        DOMElements.news.resetButton.addEventListener('click', () => api.resetNews().catch(err => showModal(err.message)));
        DOMElements.news.initiativeConfirmButton.addEventListener('click', handleInitiativeConfirm);
        DOMElements.news.determineInitiativeButton.addEventListener('click', handleDetermineInitiativeClick);
        DOMElements.news.initiativeNextNewsButton.addEventListener('click', handleNextNewsClick);

        // Прокачки
        DOMElements.upgrades.backButton.addEventListener('click', () => showScreen('mainMenu'));
        DOMElements.upgrades.treeContainer.addEventListener('click', handleUpgradeTreeClick);
        DOMElements.upgrades.viewPlayersButton.addEventListener('click', fetchAndRenderPlayerUpgrades);
        
        // Таймер
        Object.values(DOMElements.headerTimers).forEach(btn => btn.addEventListener('click', () => {
            fetchAndRenderGameState();
            showScreen('timer');
        }));
        DOMElements.timer.backButton.addEventListener('click', () => showScreen('mainMenu'));
        DOMElements.timer.sessionTimerDisplay.addEventListener('click', handleSessionTimerClick);
        DOMElements.timer.startPauseButton.addEventListener('click', handleToggleTurnTimerClick);
        DOMElements.timer.nextPlayerButton.addEventListener('click', handleNextPlayerClick);
        DOMElements.timer.actionPointsSection.addEventListener('click', handleActionPointClick);
        
        // Загальні модальні вікна
        DOMElements.modals.okButton.addEventListener('click', hideModal);
        DOMElements.modals.cancelButton.addEventListener('click', hideModal);
        DOMElements.modals.confirmButton.addEventListener('click', () => {
            if (state.confirmCallback) state.confirmCallback();
            hideModal();
        });
        DOMElements.historyModal.closeButton.addEventListener('click', () => DOMElements.historyModal.overlay.classList.remove('visible'));
        DOMElements.historyModal.playerFilter.addEventListener('change', filterHistory);
        DOMElements.modals.playersUpgradesClose.addEventListener('click', () => DOMElements.modals.playersUpgrades.classList.remove('visible'));
        DOMElements.modals.playersUpgradesFilter.addEventListener('change', renderFilteredPlayerUpgrades);
        DOMElements.modals.playersMissionsClose.addEventListener('click', () => DOMElements.modals.playersMissions.classList.remove('visible'));
        DOMElements.modals.playersMissionsFilter.addEventListener('change', renderFilteredPlayerMissions);

        // Інші глобальні обробники
        document.body.addEventListener('click', (event) => {
            const header = event.target.closest('.bot-details-header');
            if (header) {
                const item = header.parentElement;
                item.classList.toggle('open');
            }
        });

        // --- Socket.IO та початкове завантаження ---
        socket.on('update_required', async (data) => {
            console.log('Update required:', data.reason);
            const myNickname = sessionStorage.getItem('kpk_nickname');
            if (data.reason === 'game_reset') {
                showModal("Гру було скинуто адміністратором.");
                sessionStorage.removeItem('kpk_nickname');
                setTimeout(() => window.location.reload(), 2000);
                return;
            }
            if (data.reason === 'new_player' && DOMElements.screens.login.classList.contains('visible')) {
                initLoginScreen();
            }
            if (myNickname) {
                const sessionData = await api.checkSession();
                if (sessionData.logged_in) {
                    state.gameData = sessionData.user;
                    updateUI();
                }
                if (DOMElements.screens.mission.classList.contains('visible')) await fetchAndRenderMissions();
                if (DOMElements.screens.score.classList.contains('visible')) fetchAndRenderScoreScreen();
                if (DOMElements.screens.upgrades.classList.contains('visible')) await fetchAndRenderUpgrades();
                if (DOMElements.modals.playersUpgrades.classList.contains('visible')) fetchAndRenderPlayerUpgrades();
                if (DOMElements.modals.playersMissions.classList.contains('visible')) fetchAndRenderPlayerMissions();
                if (data.reason === 'action_points_updated' && data.nickname === myNickname) {
                   await fetchAndRenderGameState();
                }
            }
        });

        socket.on('game_state_updated', async () => {
            console.log('Game state updated via socket.');
            await fetchAndRenderGameState();
            const visibleScreen = document.querySelector('.screen-container.visible');
            if (!visibleScreen) return;
            switch (visibleScreen.id) {
                case 'news-screen':
                    await handleNewsScreenOpen();
                    break;
                case 'upgrades-screen':
                     await fetchAndRenderUpgrades();
                     break;
                case 'mission-screen':
                     await fetchAndRenderMissions();
                     break;
            }
        });
        
        try {
            const sessionData = await api.checkSession();
            if (sessionData.logged_in) {
                state.gameData = sessionData.user;
                updateUI();
                showScreen('mainMenu');
                await fetchAndRenderGameState();
            } else {
                sessionStorage.removeItem('kpk_nickname');
                showScreen('login');
            }
        } catch (error) {
            console.error("Session check failed on init", error);
            showScreen('login');
        }
    }

    initialize();
});