(function () {
    if (!window.Vue) {
        console.warn('Vue is not loaded; game components will not initialise.');
        return;
    }

    const { createApp, ref, reactive, computed, onMounted, watch } = Vue;

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

    const shuffle = function (array) {
        const copy = array.slice();
        for (let i = copy.length - 1; i > 0; i -= 1) {
            const j = Math.floor(Math.random() * (i + 1));
            [copy[i], copy[j]] = [copy[j], copy[i]];
        }
        return copy;
    };

    const LetterSequenceGame = {
        name: 'LetterSequenceGame',
        props: {
            word: { type: String, default: '' },
            definition: { type: String, default: '' },
            bridgeEl: { type: Object, required: true },
        },
        setup(props) {
            const normalized = computed(() => (props.word || '').replace(/\s+/g, '').toUpperCase());
            const tiles = ref([]);
            const answer = ref([]);
            const errorMessage = ref('');
            const definitionVisible = ref(false);
            const completed = ref(false);
            const missing = computed(() => normalized.value.length === 0);

            const buildTiles = () => {
                if (!normalized.value) {
                    tiles.value = [];
                    return;
                }
                const letters = normalized.value.split('').map((letter, index) => ({
                    id: `${index}-${letter}-${Math.random().toString(36).slice(2, 6)}`,
                    letter,
                    used: false,
                }));
                tiles.value = shuffle(letters);
            };

            const resetGame = () => {
                completed.value = false;
                answer.value = [];
                errorMessage.value = '';
                definitionVisible.value = false;
                buildTiles();
                emitState(props.bridgeEl, { canSubmit: false });
            };

            const selectTile = (tile) => {
                if (tile.used || completed.value) {
                    return;
                }
                tile.used = true;
                answer.value.push(tile.letter);
                errorMessage.value = '';
                checkAnswer();
            };

            const checkAnswer = () => {
                if (answer.value.length !== normalized.value.length) {
                    return;
                }
                if (answer.value.join('') === normalized.value) {
                    completed.value = true;
                    definitionVisible.value = true;
                    emitState(props.bridgeEl, {
                        canSubmit: false,
                        autoComplete: true,
                        completedLabel: 'Completed',
                    });
                } else {
                    errorMessage.value = 'Not quite right. Reset and try again.';
                }
            };

            watch(
                () => props.word,
                () => {
                    resetGame();
                }
            );

            onMounted(() => {
                if (missing.value) {
                    emitState(props.bridgeEl, { canSubmit: false });
                }
                resetGame();
            });

            return {
                tiles,
                answer,
                errorMessage,
                definitionVisible,
                completed,
                missing,
                selectTile,
                resetGame,
                definitionText: computed(() => props.definition || 'Definition coming soon.'),
            };
        },
        template: `
            <div class="letter-sequence-game" v-if="!missing">
                <div class="letter-sequence__bank">
                    <button
                        v-for="tile in tiles"
                        :key="tile.id"
                        class="letter-tile"
                        type="button"
                        :class="{ 'letter-tile--used': tile.used }"
                        :disabled="tile.used || completed"
                        @click="selectTile(tile)"
                    >
                        {{ tile.letter }}
                    </button>
                </div>
                <div class="letter-sequence__answer">{{ answer.join('') }}</div>
                <div class="letter-sequence__controls">
                    <button class="todo-check todo-check--ghost" type="button" @click="resetGame" :disabled="completed">Reset</button>
                </div>
                <p class="text-danger small mb-0" v-if="errorMessage">{{ errorMessage }}</p>
                <p class="text-white-50 small mb-0" v-if="definitionVisible">{{ definitionText }}</p>
            </div>
            <p class="text-white-50 small mb-0" v-else>Game content coming soon.</p>
        `,
    };

    const AdaptiveFlashcardsGame = {
        name: 'AdaptiveFlashcardsGame',
        props: {
            queueUrl: { type: String, default: '' },
            logUrl: { type: String, default: '' },
            bridgeEl: { type: Object, required: true },
            title: { type: String, default: '' },
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
            });

            const cardStartTime = ref(Date.now());
            const audioRef = ref(null);

            const emitSubmitState = (canSubmit, completedLabel) => {
                emitState(props.bridgeEl, { canSubmit, completedLabel });
            };

            const stopAudio = () => {
                if (audioRef.value) {
                    try {
                        audioRef.value.pause();
                    } catch (error) {
                        console.warn('Unable to pause audio clip', error);
                    }
                }
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
                setStatus('Tap to flip the card.');
                emitSubmitState(false);
            };

            const deckEmpty = computed(() => state.cards.length === 0);

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
                emitSubmitState(true);
            };

            const advanceQueue = () => {
                stopAudio();
                if (state.cards.length) {
                    const next = state.cards.shift();
                    setCurrentCard(next);
                    return;
                }
                showCelebration();
            };

            const logOutcome = (card, outcome, payload) => {
                if (!props.logUrl) {
                    return;
                }
                const body = Object.assign({
                    card_id: card.id,
                    outcome,
                }, payload);
                fetch(props.logUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify(body),
                }).catch((error) => {
                    console.error('Unable to log flashcard outcome:', error);
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

            const playAudio = () => {
                const card = state.currentCard;
                if (!card || !card.audio_url) {
                    return;
                }
                try {
                    stopAudio();
                    audioRef.value = new Audio(card.audio_url);
                    audioRef.value.play().catch((error) => {
                        console.warn('Unable to play audio', error);
                        setStatus('Audio unavailable. Practice aloud anyway.');
                    });
                } catch (error) {
                    console.warn('Audio initialisation failed', error);
                }
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

            const fetchQueue = () => {
                if (!props.queueUrl) {
                    state.loading = false;
                    state.statusText = 'No review queue configured.';
                    emitSubmitState(false);
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
                        state.cards = Array.isArray(data.cards) ? data.cards.slice() : [];
                        state.missed = [];
                        resetScoreboard();
                        state.loading = false;
                        if (!state.cards.length) {
                            setStatus('Nothing due right now. Tap “Mark Done” to keep momentum.');
                            emitSubmitState(true);
                            state.celebration = true;
                            return;
                        }
                        setCurrentCard(state.cards.shift());
                    })
                    .catch((error) => {
                        console.error('Unable to load flashcards:', error);
                        state.loading = false;
                        setStatus('Unable to load cards. Refresh the page to try again.');
                        emitSubmitState(false);
                    });
            };

            onMounted(() => {
                emitSubmitState(false);
                fetchQueue();
            });

            return {
                state,
                revealCard,
                playAudio,
                handleOutcome,
                replayMissed,
            };
        },
        template: `
            <div class="adaptive-flashcard-game">
                <div class="flashcard-stage" v-if="state.currentCard || state.loading">
                    <div class="flashcard-card" :class="{ 'is-flipped': state.isFlipped }" @click="revealCard">
                        <div class="flashcard-face flashcard-face--front">
                            <div class="flashcard-media">
                                <template v-if="state.currentCard && state.currentCard.image_url">
                                    <img class="flashcard-image" :src="state.currentCard.image_url" alt="Flashcard prompt" />
                                </template>
                                <template v-else>
                                    <div class="flashcard-placeholder">Tap to flip</div>
                                </template>
                            </div>
                        </div>
                        <div class="flashcard-face flashcard-face--back">
                            <div class="flashcard-word">{{ state.currentCard ? state.currentCard.word.toUpperCase() : '' }}</div>
                            <button class="todo-check todo-check--ghost" type="button" @click.stop="playAudio" :disabled="!(state.currentCard && state.currentCard.audio_url)">Play audio</button>
                            <p class="text-white-50 small mb-0 flashcard-pronounce-hint">Listen and repeat aloud three times.</p>
                        </div>
                    </div>
                </div>
                <div class="flashcard-empty" v-if="state.celebration">
                    <div class="flashcard-empty__icon" aria-hidden="true">🎉</div>
                    <p class="h6 mb-1">All done for now!</p>
                    <p class="text-white-50 small mb-3">{{ state.statusText }}</p>
                    <button class="todo-check" type="button" @click="replayMissed" v-if="state.replayVisible">Replay missed cards</button>
                </div>
                <div class="flashcard-scoreboard">
                    <div class="flashcard-score">{{ state.points }} pts</div>
                    <div class="flashcard-streak">Streak · {{ state.streak }}</div>
                    <div class="flashcard-reviewed">Reviewed · {{ state.reviewed }}</div>
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

    const GAME_COMPONENTS = {
        'letter-sequence': LetterSequenceGame,
        'adaptive-flashcards': AdaptiveFlashcardsGame,
    };

    const initGames = function () {
        document.querySelectorAll('.vue-game').forEach(function (mountEl) {
            const type = mountEl.dataset.gameType;
            const component = GAME_COMPONENTS[type];
            if (!component) {
                console.warn('No Vue component found for game type', type);
                return;
            }
            let props = {};
            if (mountEl.dataset.gameProps) {
                try {
                    props = JSON.parse(mountEl.dataset.gameProps);
                } catch (error) {
                    console.warn('Unable to parse game props for', type, error);
                }
            }
            props.bridgeEl = mountEl;
            createApp(component, props).mount(mountEl);
        });
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGames);
    } else {
        initGames();
    }
})();
