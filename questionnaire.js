// Ruby's Gifts Questionnaire System
// Advanced chip-based interface with search, multi-select, and accessibility

class QuestionnaireSystem {
    constructor() {
        this.currentQuestionIndex = 0;
        this.answers = {};
        this.selectedChips = {};
        this.questions = this.initializeQuestions();
        this.totalQuestions = this.questions.length;
        
        // Performance optimization: cache DOM elements
        this.elements = {
            landing: document.getElementById('landing'),
            questionnaire: document.getElementById('questionnaire'),
            results: document.getElementById('results'),
            loading: document.getElementById('loading'),
            errorMessage: document.getElementById('error-message'),
            questionContainer: document.getElementById('question-container'),
            progressFill: document.getElementById('progress-fill'),
            currentQuestion: document.getElementById('current-question'),
            totalQuestions: document.getElementById('total-questions'),
            prevBtn: document.getElementById('prev-btn'),
            nextBtn: document.getElementById('next-btn'),
            submitBtn: document.getElementById('submit-btn'),
            startBtn: document.getElementById('start-btn'),
            retryBtn: document.getElementById('retry-btn'),
            newSearchBtn: document.getElementById('new-search-btn'),
            errorRetryBtn: document.getElementById('error-retry-btn'),
            giftCards: document.getElementById('gift-cards')
        };
        
        this.debounceTimeout = null;
        this.init();
    }

    initializeQuestions() {
        return [
            {
                id: 'nicknames',
                title: 'what do you call them?',
                chipData: CHIP_DATA.nicknames,
                required: true,
                placeholder: 'e.g., buddy, sweetheart, their name...'
            },
            {
                id: 'relationships',
                title: 'what\'s your relationship?',
                chipData: CHIP_DATA.relationships,
                required: true,
                placeholder: 'e.g., best friend, sibling, romantic partner...'
            },
            {
                id: 'previousGifts',
                title: 'what have you already gifted them?',
                chipData: CHIP_DATA.previousGifts,
                required: true,
                placeholder: 'e.g., jewelry, books, experiences...'
            },
            {
                id: 'dislikes',
                title: 'what will they absolutely hate?',
                chipData: CHIP_DATA.dislikes,
                required: true,
                placeholder: 'e.g., spiders, loud noises, cheap items...'
            },
            {
                id: 'complaints',
                title: 'what do they keep complaining about?',
                chipData: CHIP_DATA.complaints,
                required: true,
                placeholder: 'e.g., work stress, traffic, technology issues...'
            },
            {
                id: 'quirks',
                title: 'how would you complain about them to someone?',
                chipData: CHIP_DATA.quirks,
                required: false,
                placeholder: 'e.g., always late, too picky, perfectionist...'
            },
            {
                id: 'budget',
                title: 'what\'s your budget?',
                chipData: CHIP_DATA.budget,
                required: true,
                placeholder: 'e.g., ₹500-1000, luxury splurge, budget-friendly...'
            },
            {
                id: 'limitations',
                title: 'any other limitations?',
                chipData: CHIP_DATA.limitations,
                required: false,
                placeholder: 'e.g., eco-friendly, portable, personalized...'
            }
        ];
    }

    init() {
        this.bindEvents();
        this.updateProgressBar();
        this.elements.totalQuestions.textContent = this.totalQuestions;
        
        // Initialize first question when questionnaire is shown
        this.renderCurrentQuestion();
    }

    bindEvents() {
        // Page navigation
        this.elements.startBtn.addEventListener('click', () => this.showQuestionnaire());
        this.elements.prevBtn.addEventListener('click', () => this.previousQuestion());
        this.elements.nextBtn.addEventListener('click', () => this.nextQuestion());
        this.elements.submitBtn.addEventListener('click', () => this.submitQuestionnaire());
        
        // Results actions
        this.elements.retryBtn.addEventListener('click', () => this.resetQuestionnaire());
        this.elements.newSearchBtn.addEventListener('click', () => this.resetQuestionnaire());
        this.elements.errorRetryBtn.addEventListener('click', () => this.hideError());

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyNavigation(e));
    }

    showQuestionnaire() {
        this.elements.landing.classList.remove('active');
        this.elements.questionnaire.classList.add('active');
        this.renderCurrentQuestion();
        
        // Focus management for accessibility
        setTimeout(() => {
            const searchInput = document.querySelector('.search-input');
            if (searchInput) searchInput.focus();
        }, 100);
    }

    renderCurrentQuestion() {
        const question = this.questions[this.currentQuestionIndex];
        if (!question) return;

        // Create question HTML structure
        const questionHTML = `
            <div class="question" data-question-id="${question.id}">
                <h2 class="question-title">${question.title}</h2>
                
                <div class="search-container">
                    <i class="ph ph-magnifying-glass search-icon"></i>
                    <input 
                        type="text" 
                        class="search-input" 
                        placeholder="search options..." 
                        aria-label="Search ${question.title} options"
                        autocomplete="off"
                    >
                </div>

                <div class="chip-grid" 
                     role="grid" 
                     aria-label="${question.title} options"
                     data-question-id="${question.id}">
                    <!-- Chips will be rendered here -->
                </div>

                <div class="answer-container">
                    <label class="answer-label" for="answer-${question.id}">
                        your answer (edit as needed):
                    </label>
                    <textarea 
                        class="answer-input"
                        id="answer-${question.id}"
                        placeholder="${question.placeholder}"
                        aria-describedby="answer-help-${question.id}"
                        ${question.required ? 'required' : ''}
                    ></textarea>
                    <div id="answer-help-${question.id}" class="sr-only">
                        Select chips above or type your custom answer. Multiple selections will be combined.
                    </div>
                </div>
            </div>
        `;

        this.elements.questionContainer.innerHTML = questionHTML;
        
        // Render chips and bind events
        this.renderChips(question);
        this.bindQuestionEvents(question);
        this.restoreQuestionState(question);
        this.updateNavigation();
        this.updateProgressBar();
    }

    renderChips(question) {
        const chipGrid = document.querySelector(`[data-question-id="${question.id}"]`);
        if (!chipGrid) return;

        // Use DocumentFragment for better performance
        const fragment = document.createDocumentFragment();
        
        question.chipData.forEach((chip, index) => {
            const chipElement = this.createChipElement(chip, question.id, index);
            fragment.appendChild(chipElement);
        });

        chipGrid.appendChild(fragment);
    }

    createChipElement(chip, questionId, index) {
        const chipElement = document.createElement('div');
        chipElement.className = 'chip';
        chipElement.setAttribute('role', 'gridcell');
        chipElement.setAttribute('tabindex', '0');
        chipElement.setAttribute('aria-label', chip.text);
        chipElement.setAttribute('data-chip-text', chip.text);
        chipElement.setAttribute('data-question-id', questionId);
        chipElement.setAttribute('data-chip-index', index);

        // Check if chip should be selected
        const isSelected = this.selectedChips[questionId]?.includes(chip.text);
        if (isSelected) {
            chipElement.classList.add('selected');
            chipElement.setAttribute('aria-selected', 'true');
        } else {
            chipElement.setAttribute('aria-selected', 'false');
        }

        chipElement.innerHTML = `
            <i class="ph ${chip.icon} chip-icon" aria-hidden="true"></i>
            <span class="chip-text">${chip.text}</span>
        `;

        // Bind click and keyboard events
        chipElement.addEventListener('click', () => this.toggleChip(chipElement, chip, questionId));
        chipElement.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleChip(chipElement, chip, questionId);
            }
        });

        return chipElement;
    }

    bindQuestionEvents(question) {
        const searchInput = document.querySelector('.search-input');
        const answerInput = document.querySelector(`#answer-${question.id}`);

        if (searchInput) {
            // Debounced search for better performance
            searchInput.addEventListener('input', (e) => {
                clearTimeout(this.debounceTimeout);
                this.debounceTimeout = setTimeout(() => {
                    this.filterChips(e.target.value, question.id);
                }, 150);
            });
        }

        if (answerInput) {
            // Save answer on input and sync with chip states
            answerInput.addEventListener('input', (e) => {
                this.answers[question.id] = e.target.value;
                this.syncTextareaToChips(question.id, e.target.value);
                this.updateNavigation();
            });

            // Handle manual editing mode
            answerInput.addEventListener('focus', () => {
                answerInput.setAttribute('data-manual-edit', 'true');
            });

            // Re-enable auto-sync when user clicks elsewhere
            answerInput.addEventListener('blur', () => {
                // Small delay to allow for chip clicks
                setTimeout(() => {
                    answerInput.removeAttribute('data-manual-edit');
                }, 200);
            });
        }
    }

    toggleChip(chipElement, chip, questionId) {
        const isSelected = chipElement.classList.contains('selected');
        
        if (isSelected) {
            // Deselect chip
            chipElement.classList.remove('selected');
            chipElement.setAttribute('aria-selected', 'false');
            this.removeChipFromSelection(chip.text, questionId);
        } else {
            // Select chip
            chipElement.classList.add('selected');
            chipElement.setAttribute('aria-selected', 'true');
            this.addChipToSelection(chip.text, questionId);
        }

        // Announce change to screen readers
        this.announceChipChange(chip.text, !isSelected);
        
        this.updateAnswerInput(questionId);
        this.updateNavigation();
    }

    // Methods moved to end of class with enhancements

    updateAnswerInput(questionId) {
        const answerInput = document.querySelector(`#answer-${questionId}`);
        if (!answerInput) return;

        // Don't override if user is manually editing
        if (answerInput.getAttribute('data-manual-edit') === 'true') return;

        const selectedChips = this.selectedChips[questionId] || [];
        const currentValue = answerInput.value.trim();
        
        // Merge existing custom text with selected chips
        const chipTexts = selectedChips.filter(text => text.trim().length > 0);
        const customTexts = this.extractCustomText(currentValue, chipTexts);
        
        // Combine chips and custom text, removing duplicates
        const allTexts = [...chipTexts, ...customTexts].filter((text, index, arr) => 
            arr.indexOf(text) === index && text.trim().length > 0
        );
        
        const finalText = allTexts.join(', ');
        answerInput.value = finalText;
        this.answers[questionId] = finalText;
    }

    filterChips(searchTerm, questionId) {
        const chipGrid = document.querySelector(`[data-question-id="${questionId}"]`);
        if (!chipGrid) return;

        const chips = chipGrid.querySelectorAll('.chip');
        const normalizedSearch = searchTerm.toLowerCase().trim();
        let visibleCount = 0;

        chips.forEach(chip => {
            const chipText = chip.getAttribute('data-chip-text').toLowerCase();
            const isMatch = chipText.includes(normalizedSearch) || 
                           this.fuzzyMatch(chipText, normalizedSearch);
            
            if (isMatch || !searchTerm) {
                chip.style.display = 'flex';
                visibleCount++;
            } else {
                chip.style.display = 'none';
            }
        });

        // Show "no results" message if needed
        this.toggleNoResultsMessage(chipGrid, visibleCount === 0 && searchTerm);
    }

    fuzzyMatch(text, search) {
        // Simple fuzzy matching for typos
        if (search.length < 3) return false;
        
        let searchIndex = 0;
        for (let i = 0; i < text.length && searchIndex < search.length; i++) {
            if (text[i] === search[searchIndex]) {
                searchIndex++;
            }
        }
        return searchIndex === search.length;
    }

    toggleNoResultsMessage(chipGrid, show) {
        let noResults = chipGrid.querySelector('.no-results');
        
        if (show && !noResults) {
            noResults = document.createElement('div');
            noResults.className = 'no-results';
            noResults.innerHTML = `
                <div class="no-results-icon">
                    <i class="ph ph-magnifying-glass"></i>
                </div>
                <div class="no-results-text">
                    no matching options found.<br>
                    try a different search or type your custom answer below.
                </div>
            `;
            chipGrid.appendChild(noResults);
        } else if (!show && noResults) {
            noResults.remove();
        }
    }

    restoreQuestionState(question) {
        // Restore previous answer
        const answerInput = document.querySelector(`#answer-${question.id}`);
        if (answerInput && this.answers[question.id]) {
            answerInput.value = this.answers[question.id];
            // Sync textarea content back to chip states
            this.syncTextareaToChips(question.id, this.answers[question.id]);
        }

        // Ensure visual states match the data
        this.updateChipVisualStates(question.id);
        
        // Reset manual edit flag
        if (answerInput) {
            answerInput.removeAttribute('data-manual-edit');
        }
    }

    previousQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.saveCurrentAnswer();
            this.currentQuestionIndex--;
            this.renderCurrentQuestion();
        }
    }

    nextQuestion() {
        if (this.currentQuestionIndex < this.totalQuestions - 1) {
            this.saveCurrentAnswer();
            this.currentQuestionIndex++;
            this.renderCurrentQuestion();
        }
    }

    saveCurrentAnswer() {
        const question = this.questions[this.currentQuestionIndex];
        const answerInput = document.querySelector(`#answer-${question.id}`);
        
        if (answerInput) {
            this.answers[question.id] = answerInput.value;
        }
    }

    updateNavigation() {
        const question = this.questions[this.currentQuestionIndex];
        const isFirstQuestion = this.currentQuestionIndex === 0;
        const isLastQuestion = this.currentQuestionIndex === this.totalQuestions - 1;
        const hasValidAnswer = this.hasValidAnswer(question);

        // Update button states
        this.elements.prevBtn.disabled = isFirstQuestion;
        this.elements.nextBtn.style.display = isLastQuestion ? 'none' : 'inline-flex';
        this.elements.submitBtn.style.display = isLastQuestion ? 'inline-flex' : 'none';
        
        // Enable next/submit only if current question is valid
        if (isLastQuestion) {
            this.elements.submitBtn.disabled = !hasValidAnswer || !this.allRequiredAnswered();
        } else {
            this.elements.nextBtn.disabled = !hasValidAnswer;
        }
    }

    hasValidAnswer(question) {
        const answer = this.answers[question.id];
        return !question.required || (answer && answer.trim().length > 0);
    }

    allRequiredAnswered() {
        return this.questions.every(question => {
            return !question.required || this.hasValidAnswer(question);
        });
    }

    updateProgressBar() {
        const progress = ((this.currentQuestionIndex + 1) / this.totalQuestions) * 100;
        this.elements.progressFill.style.width = `${progress}%`;
        this.elements.currentQuestion.textContent = this.currentQuestionIndex + 1;
    }

    handleKeyNavigation(e) {
        // Global keyboard shortcuts
        if (e.altKey || e.ctrlKey || e.metaKey) return;

        switch (e.key) {
            case 'ArrowLeft':
                if (document.activeElement.tagName !== 'INPUT' && 
                    document.activeElement.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    if (!this.elements.prevBtn.disabled) this.previousQuestion();
                }
                break;
            case 'ArrowRight':
                if (document.activeElement.tagName !== 'INPUT' && 
                    document.activeElement.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    if (!this.elements.nextBtn.disabled && this.elements.nextBtn.style.display !== 'none') {
                        this.nextQuestion();
                    } else if (!this.elements.submitBtn.disabled && this.elements.submitBtn.style.display !== 'none') {
                        this.submitQuestionnaire();
                    }
                }
                break;
            case 'Escape':
                // Close any modals or return to previous state
                if (this.elements.errorMessage.classList.contains('active')) {
                    this.hideError();
                }
                break;
        }
    }

    async submitQuestionnaire() {
        this.saveCurrentAnswer();
        
        // Validate all required answers
        if (!this.allRequiredAnswered()) {
            this.showError('Please answer all required questions before submitting.');
            return;
        }

        this.showLoading();
        
        try {
            // Simulate API call for now - replace with actual backend call
            await this.generateGiftIdeas();
            this.showResults();
        } catch (error) {
            console.error('Error generating gift ideas:', error);
            this.showError('Failed to generate gift ideas. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    async generateGiftIdeas() {
        try {
            // Prepare API request data
            const requestData = {
                call_them: this.answers.nicknames || '',
                relationship: this.answers.relationships || '',
                previous_gifts: this.answers.previousGifts || '',
                hate: this.answers.dislikes || '',
                complaints: this.answers.complaints || '',
                complain_about_them: this.answers.quirks || '',
                budget: this.answers.budget || '',
                limitations: this.answers.limitations || ''
            };
            
            // Call the Flask API
            const response = await fetch('/generate_gifts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`API call failed with status ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.gift_ideas) {
                this.renderGiftCards(data.gift_ideas);
            } else {
                throw new Error('Invalid response format from API');
            }
            
        } catch (error) {
            console.error('Error generating gift ideas:', error);
            
            // Fallback to mock data if API fails
            console.log('Falling back to mock data...');
            const mockGifts = [
                {
                    title: 'personalized photo album',
                    description: 'A custom photo book filled with your favorite memories together. Perfect for someone who appreciates sentimental gifts and personal touches.',
                    starter: 'You could say: "I made this photo album of our favorite memories together."',
                    reaction: 'They might smile and flip through it immediately, pointing out their favorite photos.'
                },
                {
                    title: 'premium coffee subscription',
                    description: 'Monthly delivery of specialty coffee beans from around the world. Great for coffee lovers who enjoy trying new flavors.',
                    starter: 'You could mention: "I got you a coffee subscription so you can try beans from different countries."',
                    reaction: 'They might get excited about trying new flavors and ask which countries are included.'
                },
                {
                    title: 'wireless noise-canceling headphones',
                    description: 'High-quality headphones perfect for music lovers or anyone who needs to focus in noisy environments.',
                    starter: 'You could say: "These headphones should help you focus better when things get noisy."',
                    reaction: 'They might immediately want to test them out and ask about the noise-canceling features.'
                }
            ];
            
            this.renderGiftCards(mockGifts);
        }
    }

    renderGiftCards(gifts) {
        const cardsHTML = gifts.map(gift => `
            <div class="gift-card">
                <h3 class="gift-card-title">${gift.title}</h3>
                <p class="gift-card-description">${gift.description}</p>
                ${gift.starter ? `<div class="gift-card-starter"><strong>How to present it:</strong> ${gift.starter}</div>` : ''}
                ${gift.reaction ? `<div class="gift-card-reaction"><strong>Expected reaction:</strong> ${gift.reaction}</div>` : ''}
                ${gift.price ? `<div class="gift-card-price">${gift.price}</div>` : ''}
            </div>
        `).join('');
        
        this.elements.giftCards.innerHTML = cardsHTML;
    }

    showLoading() {
        this.elements.loading.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    hideLoading() {
        this.elements.loading.classList.remove('active');
        document.body.style.overflow = '';
    }

    showResults() {
        this.elements.questionnaire.classList.remove('active');
        this.elements.results.classList.add('active');
        
        // Announce to screen readers
        this.announceToScreenReader('Gift recommendations loaded successfully');
    }

    showError(message) {
        document.getElementById('error-text').textContent = message;
        this.elements.errorMessage.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Focus error dialog for accessibility
        setTimeout(() => {
            this.elements.errorRetryBtn.focus();
        }, 100);
    }

    hideError() {
        this.elements.errorMessage.classList.remove('active');
        document.body.style.overflow = '';
    }

    resetQuestionnaire() {
        // Reset state
        this.currentQuestionIndex = 0;
        this.answers = {};
        this.selectedChips = {};
        
        // Return to landing page
        this.elements.results.classList.remove('active');
        this.elements.questionnaire.classList.remove('active');
        this.elements.landing.classList.add('active');
        
        // Clear any error states
        this.hideError();
        
        // Reset progress
        this.updateProgressBar();
    }

    announceChipChange(chipText, isSelected) {
        const action = isSelected ? 'selected' : 'deselected';
        this.announceToScreenReader(`${chipText} ${action}`);
    }

    announceToScreenReader(message) {
        // Create temporary element for screen reader announcements
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        // Remove after announcement
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    // NEW METHODS FOR ENHANCED MULTI-SELECT FUNCTIONALITY
    
    syncTextareaToChips(questionId, textareaValue) {
        // Parse textarea content to update chip states
        if (!textareaValue || textareaValue.trim().length === 0) {
            // Clear all selections if textarea is empty
            this.selectedChips[questionId] = [];
            this.updateChipVisualStates(questionId);
            return;
        }

        // Split by comma and clean up text
        const textItems = textareaValue.split(',').map(item => item.trim()).filter(item => item.length > 0);
        
        // Find which items match available chips
        const question = this.questions.find(q => q.id === questionId);
        if (!question) return;

        const availableChipTexts = question.chipData.map(chip => chip.text.toLowerCase());
        const matchingChips = textItems.filter(item => 
            availableChipTexts.includes(item.toLowerCase())
        );

        // Update selected chips to match textarea content
        this.selectedChips[questionId] = matchingChips;
        this.updateChipVisualStates(questionId);
    }

    updateChipVisualStates(questionId) {
        // Update visual states of all chips for a question
        const chipElements = document.querySelectorAll(`[data-question-id="${questionId}"].chip`);
        const selectedTexts = (this.selectedChips[questionId] || []).map(text => text.toLowerCase());

        chipElements.forEach(chipElement => {
            const chipText = chipElement.getAttribute('data-chip-text').toLowerCase();
            const shouldBeSelected = selectedTexts.includes(chipText);
            
            if (shouldBeSelected) {
                chipElement.classList.add('selected');
                chipElement.setAttribute('aria-selected', 'true');
            } else {
                chipElement.classList.remove('selected');
                chipElement.setAttribute('aria-selected', 'false');
            }
        });
    }

    extractCustomText(currentValue, chipTexts) {
        // Extract custom text that's not from chips
        if (!currentValue) return [];
        
        const allItems = currentValue.split(',').map(item => item.trim()).filter(item => item.length > 0);
        const chipTextsLower = chipTexts.map(text => text.toLowerCase());
        
        return allItems.filter(item => !chipTextsLower.includes(item.toLowerCase()));
    }

    addChipToSelection(chipText, questionId) {
        if (!this.selectedChips[questionId]) {
            this.selectedChips[questionId] = [];
        }
        
        // Enhanced duplicate prevention - case insensitive
        const existingTexts = this.selectedChips[questionId].map(text => text.toLowerCase());
        if (!existingTexts.includes(chipText.toLowerCase())) {
            this.selectedChips[questionId].push(chipText);
        }
    }

    removeChipFromSelection(chipText, questionId) {
        if (this.selectedChips[questionId]) {
            // Case-insensitive removal
            this.selectedChips[questionId] = this.selectedChips[questionId].filter(
                text => text.toLowerCase() !== chipText.toLowerCase()
            );
        }
    }
}

// Screen reader only class
const style = document.createElement('style');
style.textContent = `
    .sr-only {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        padding: 0 !important;
        margin: -1px !important;
        overflow: hidden !important;
        clip: rect(0, 0, 0, 0) !important;
        white-space: nowrap !important;
        border: 0 !important;
    }
`;
document.head.appendChild(style);

// Initialize the questionnaire system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new QuestionnaireSystem();
});