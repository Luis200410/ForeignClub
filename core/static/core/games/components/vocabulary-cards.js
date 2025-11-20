(function () {
    if (!window.Vue) {
        console.warn('Vue is not loaded; vocabulary cards will not initialise.');
        return;
    }

    const { reactive, ref, onMounted } = window.Vue;

    const normaliseCards = (cards) => {
        if (!Array.isArray(cards)) {
            return [];
        }
        const seen = new Set();
        return cards
            .map((card) => {
                const id = card && card.id ? Number(card.id) : null;
                const word = card && card.word ? String(card.word).trim() : '';
                const meaning = card && card.meaning ? String(card.meaning).trim() : '';
                return { id, word, meaning };
            })
            .filter((card) => {
                if (!card.id || !card.word) {
                    return false;
                }
                if (seen.has(card.id)) {
                    return false;
                }
                seen.add(card.id);
                return true;
            });
    };

    const getCsrfToken = function () {
        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return input ? input.value : '';
    };

    const emitState = function (bridgeEl, detail) {
        if (!bridgeEl) {
            return;
        }
        bridgeEl.dispatchEvent(
            new CustomEvent('game:state', {
                detail,
                bubbles: false,
            })
        );
    };

    const VocabularyCardsGame = {
        name: 'VocabularyCardsGame',
        props: {
            queueUrl: { type: String, default: '' },
            logUrl: { type: String, default: '' },
            bridgeEl: { type: Object, required: true },
            title: { type: String, default: '' },
            analyticsUrl: { type: String, default: '' },
            initialCards: {
                type: Array,
                default: () => [],
            },
        },
        setup(props) {
            const state = reactive({
                loading: true,
                cards: [],
                missed: [],
                currentCard: null,
                isFlipped: false,
                statusText: 'Loading cards…',
                points: 0,
                streak: 0,
                reviewed: 0,
                replayVisible: false,
                celebration: false,
                canReviewAll: false,
            });

            const analytics = reactive({
                loading: false,
                totalPoints: 0,
                totalReviewed: 0,
                accuracy: 0,
                dueNow: 0,
                totalActive: 0,
                missed: [],
                recent: [],
            });

            const cardStartTime = ref(Date.now());
            const initialDeck = ref(normaliseCards(props.initialCards));

            const hasInitialDeck = () => initialDeck.value.length > 0;

            const refreshReviewButton = () => {
                state.canReviewAll = hasInitialDeck();
            };

            refreshReviewButton();

            const emitSubmitState = (canSubmit, completedLabel) => {
                emitState(props.bridgeEl, { canSubmit, completedLabel });
            };

            const setStatus = (text) => {
                state.statusText = text || '';
            };

            const resetScoreboard = () => {
                state.points = 0;
                state.streak = 0;
                state.reviewed = 0;
            };

            const setCurrentCard = (card) => {
                state.currentCard = card;
                state.isFlipped = false;
                cardStartTime.value = Date.now();
                state.celebration = false;
                state.replayVisible = false;
                setStatus('Tap the card to see the meaning.');
                emitSubmitState(false);
            };

            const showCelebration = () => {
                state.currentCard = null;
                state.celebration = true;
                if (state.missed.length) {
                    state.replayVisible = true;
                    setStatus('Great work. Replay the tricky words or tap “Mark Done” to finish.');
                } else {
                    state.replayVisible = false;
                    setStatus('Daily review done. Tap “Mark Done” to lock it in.');
                }
                refreshReviewButton();
                emitSubmitState(true);
            };

            const advanceQueue = () => {
                if (state.cards.length) {
                    const next = state.cards.shift();
                    setCurrentCard(next);
                    return;
                }
                showCelebration();
            };

            const refreshAnalytics = () => {
                if (!props.analyticsUrl) {
                    return;
                }
                analytics.loading = true;
                fetch(props.analyticsUrl, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                })
                    .then((response) => {
                        if (!response.ok) {
                            throw new Error('Unable to load analytics');
                        }
                        return response.json();
                    })
                    .then((data) => {
                        const stats = data.stats || {};
                        analytics.totalPoints = stats.total_points || 0;
                        analytics.totalReviewed = stats.total_seen || 0;
                        analytics.accuracy = stats.accuracy || 0;
                        analytics.dueNow = stats.due_now || 0;
                        analytics.totalActive = stats.total_active || 0;
                        analytics.missed = Array.isArray(data.missed_words) ? data.missed_words : [];
                        analytics.recent = Array.isArray(data.recent_activity) ? data.recent_activity : [];
                    })
                    .catch((error) => {
                        console.warn('Unable to load flashcard analytics:', error);
                    })
                    .finally(() => {
                        analytics.loading = false;
                    });
            };

            const logOutcome = (card, outcome, payload) => {
                if (!props.logUrl) {
                    return;
                }
                const body = Object.assign(
                    {
                        card_id: card.id,
                        outcome,
                    },
                    payload
                );
                fetch(props.logUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify(body),
                })
                    .catch((error) => {
                        console.error('Unable to log flashcard outcome:', error);
                    })
                    .finally(() => {
                        refreshAnalytics();
                    });
            };

            const handleOutcome = (outcome) => {
                const card = state.currentCard;
                if (!card || !state.isFlipped || state.loading) {
                    return;
                }

                const elapsed = Math.max(0, Date.now() - cardStartTime.value);
                let pointsAwarded = 0;

                if (outcome === 'knew') {
                    state.streak += 1;
                    pointsAwarded += 10;
                    if (state.streak > 0 && state.streak % 5 === 0) {
                        pointsAwarded += 25;
                    }
                    state.missed = state.missed.filter((item) => item.id !== card.id);
                    setStatus('Nice! +' + pointsAwarded + ' pts');
                } else {
                    state.streak = 0;
                    if (!state.missed.find((item) => item.id === card.id)) {
                        state.missed.push(card);
                    }
                    setStatus('We will repeat this word shortly.');
                }

                state.points += pointsAwarded;
                state.reviewed += 1;

                logOutcome(card, outcome, {
                    points_awarded: pointsAwarded,
                    streak_length: state.streak,
                    time_spent_ms: elapsed,
                });

                state.currentCard = null;
                state.isFlipped = false;
                window.setTimeout(advanceQueue, 320);
            };

            const revealCard = () => {
                if (!state.currentCard || state.isFlipped) {
                    return;
                }
                state.isFlipped = true;
                setStatus('Did you know this word?');
            };

            const replayMissed = () => {
                if (!state.missed.length) {
                    return;
                }
                state.cards = state.missed.slice();
                state.missed = [];
                state.replayVisible = false;
                advanceQueue();
                setStatus('Replaying the words you missed.');
                emitSubmitState(false);
            };

            const startFullReview = (auto = false) => {
                const deck = initialDeck.value;
                if (!deck.length) {
                    refreshReviewButton();
                    return false;
                }
                const cards = deck.map((entry) => ({
                    id: entry.id,
                    word: entry.word,
                    meaning: entry.meaning,
                }));
                resetScoreboard();
                state.cards = cards.slice(1);
                state.missed = [];
                state.celebration = false;
                state.replayVisible = false;
                refreshReviewButton();
                setCurrentCard(cards[0]);
                if (auto) {
                    setStatus('Review these cards to stay sharp between live missions.');
                } else {
                    setStatus('Full-deck review activated. Let’s go.');
                }
                return true;
            };

            const fetchQueue = () => {
                if (!props.queueUrl) {
                    state.loading = false;
                    if (startFullReview(true)) {
                        return;
                    }
                    state.statusText = 'No review queue configured.';
                    emitSubmitState(false);
                    state.celebration = true;
                    return;
                }
                state.loading = true;
                setStatus('Loading cards…');
                emitSubmitState(false);
                fetch(props.queueUrl, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                })
                    .then((response) => {
                        if (!response.ok) {
                            throw new Error('Unable to load queue');
                        }
                        return response.json();
                    })
                    .then((data) => {
                        const queueCards = Array.isArray(data.cards) ? data.cards.slice() : [];
                        if (queueCards.length) {
                            state.cards = queueCards;
                            state.missed = [];
                            resetScoreboard();
                            state.loading = false;
                            state.usingFallback = false;
                            setCurrentCard(state.cards.shift());
                            refreshReviewButton();
                            return;
                        }
                        state.cards = [];
                        state.missed = [];
                        state.loading = false;
                        if (startFullReview(true)) {
                            return;
                        }
                        resetScoreboard();
                        setStatus('Nothing due right now. Tap “Mark Done” to keep momentum.');
                        emitSubmitState(true);
                        state.celebration = true;
                        refreshReviewButton();
                    })
                    .catch((error) => {
                        console.error('Unable to load flashcards:', error);
                        state.loading = false;
                        if (startFullReview(true)) {
                            return;
                        }
                        setStatus('Unable to load cards. Refresh the page to try again.');
                        emitSubmitState(false);
                        state.celebration = true;
                    });
            };

            onMounted(() => {
                emitSubmitState(false);
                fetchQueue();
                refreshAnalytics();
            });

            return {
                state,
                revealCard,
                handleOutcome,
                replayMissed,
                startFullReview,
                analytics,
            };
        },
        template: `
            <div class="adaptive-flashcard-game">
                <div class="flashcard-stage">
                    <div class="flashcard-card" v-if="state.currentCard || state.loading" :class="{ 'is-flipped': state.isFlipped }" @click="revealCard">
                        <div class="flashcard-face flashcard-face--front">
                            <div class="flashcard-word">{{ state.currentCard ? state.currentCard.word.toUpperCase() : '' }}</div>
                            <p class="flashcard-subtitle">{{ state.loading ? 'Loading cards…' : 'Tap to reveal the meaning' }}</p>
                        </div>
                        <div class="flashcard-face flashcard-face--back">
                            <div class="flashcard-word">{{ state.currentCard ? state.currentCard.word.toUpperCase() : '' }}</div>
                            <p class="flashcard-meaning">{{ state.currentCard && state.currentCard.meaning ? state.currentCard.meaning : 'Add the definition in the admin to display it here.' }}</p>
                            <p class="text-white-50 small mb-0 flashcard-pronounce-hint">Say it aloud three times. Use it in a sentence.</p>
                        </div>
                    </div>
                    <div class="flashcard-empty" v-else-if="state.celebration">
                        <div class="flashcard-empty__icon" aria-hidden="true">🎉</div>
                        <p class="h6 mb-1">All done for now!</p>
                        <p class="text-white-50 small mb-3">{{ state.statusText }}</p>
                        <button class="todo-check" type="button" @click="replayMissed" v-if="state.replayVisible">Replay missed cards</button>
                        <button class="todo-check todo-check--ghost" type="button" @click="startFullReview(false)" v-if="state.canReviewAll">Review all cards</button>
                    </div>
                    <div class="flashcard-empty flashcard-empty--neutral" v-else>
                        <div class="flashcard-empty__icon" aria-hidden="true">🃏</div>
                        <p class="h6 mb-1">Flashcards will show here</p>
                        <p class="text-white-50 small mb-0">{{ state.statusText || 'Add cards in the admin or refresh your queue.' }}</p>
                    </div>
                </div>
                <div class="flashcard-scoreboard">
                    <div class="flashcard-score">{{ state.points }} pts</div>
                    <div class="flashcard-streak">Streak · {{ state.streak }}</div>
                    <div class="flashcard-reviewed">Reviewed · {{ state.reviewed }}</div>
                </div>
                <div class="flashcard-analytics" v-if="analytics.totalReviewed || analytics.missed.length">
                    <div class="flashcard-analytics__stats">
                        <span class="flashcard-chip">Total pts · {{ analytics.totalPoints }}</span>
                        <span class="flashcard-chip">Accuracy · {{ analytics.accuracy }}%</span>
                        <span class="flashcard-chip">Due now · {{ analytics.dueNow }}</span>
                    </div>
                    <div class="flashcard-missed" v-if="analytics.missed.length">
                        <p class="text-white-50 small mb-1">Most missed words</p>
                        <div class="flashcard-missed__list">
                            <span class="flashcard-chip" v-for="miss in analytics.missed" :key="miss.id || miss.word">
                                {{ (miss.word || '').toUpperCase() }} · {{ miss.missed_count || 0 }}x
                            </span>
                        </div>
                    </div>
                </div>
                <div class="flashcard-controls">
                    <button class="todo-check todo-check--ghost" type="button" @click="revealCard" :disabled="state.isFlipped || !state.currentCard">Flip card</button>
                    <div class="flashcard-response-buttons">
                        <button class="todo-check todo-check--cta" type="button" @click="handleOutcome('knew')" :disabled="!state.isFlipped || !state.currentCard">I knew it</button>
                        <button class="todo-check" type="button" @click="handleOutcome('didnt')" :disabled="!state.isFlipped || !state.currentCard">I didn't</button>
                    </div>
                </div>
                <p class="text-white-50 small mb-0" v-if="state.statusText">{{ state.statusText }}</p>
            </div>
        `,
    };

    window.ForeignGames = window.ForeignGames || {};
    window.ForeignGames.VocabularyCards = VocabularyCardsGame;
})();
