// Ruby's Gifts Questionnaire System
// Advanced chip-based interface with multi-select and accessibility

class QuestionnaireSystem {
    constructor() {
        this.currentQuestionIndex = 0;
        this.answers = {};
        this.selectedChips = {};
        this.questions = this.initializeQuestions();
        this.totalQuestions = this.questions.length;
        
        // Performance optimization: cache DOM elements with error handling
        this.elements = this.cacheElements();
        
        this.debounceTimeout = null;
        this.init();
    }

    cacheElements() {
        const elements = {};
        const elementIds = [
            'landing', 'questionnaire', 'results', 'loading', 'error-message',
            'question-container', 'progress-fill', 'current-question', 'total-questions',
            'prev-btn', 'next-btn', 'submit-btn', 'start-btn', 'test-btn',
            'retry-btn', 'new-search-btn', 'error-retry-btn', 'gift-cards'
        ];
        
        elementIds.forEach(id => {
            const element = document.getElementById(id);
            if (!element) {
                console.warn(`DOM element with id '${id}' not found`);
            }
            elements[this.toCamelCase(id)] = element;
        });
        
        return elements;
    }

    toCamelCase(str) {
        return str.replace(/-([a-z])/g, (match, letter) => letter.toUpperCase());
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
        
        // Set total questions with null check
        if (this.elements.totalQuestions) {
            this.elements.totalQuestions.textContent = this.totalQuestions;
        }
        
        // Initialize first question when questionnaire is shown
        this.renderCurrentQuestion();
    }

    bindEvents() {
        // Page navigation - add null checks for each element
        if (this.elements.startBtn) {
            this.elements.startBtn.addEventListener('click', () => this.showQuestionnaire());
        }
        
        if (this.elements.testBtn) {
            this.elements.testBtn.addEventListener('click', () => this.testGiftGeneration());
        }
        
        if (this.elements.prevBtn) {
            this.elements.prevBtn.addEventListener('click', () => this.previousQuestion());
        }
        
        if (this.elements.nextBtn) {
            this.elements.nextBtn.addEventListener('click', () => this.nextQuestion());
        }
        
        if (this.elements.submitBtn) {
            this.elements.submitBtn.addEventListener('click', () => this.submitQuestionnaire());
        }
        
        // Results actions
        if (this.elements.retryBtn) {
            this.elements.retryBtn.addEventListener('click', () => this.resetQuestionnaire());
        }
        
        if (this.elements.newSearchBtn) {
            this.elements.newSearchBtn.addEventListener('click', () => this.resetQuestionnaire());
        }
        
        if (this.elements.errorRetryBtn) {
            this.elements.errorRetryBtn.addEventListener('click', () => this.hideError());
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyNavigation(e));
    }

    showQuestionnaire() {
        if (this.elements.landing) {
            this.elements.landing.classList.remove('active');
        }
        
        if (this.elements.questionnaire) {
            this.elements.questionnaire.classList.add('active');
        }
        
        // Add fixed navigation class for progress bar styling
        const progressContainer = document.querySelector('.progress-container');
        if (progressContainer) {
            progressContainer.classList.add('fixed-nav');
        }
        
        this.renderCurrentQuestion();
        
        // Focus management for accessibility
        setTimeout(() => {
            const firstChip = document.querySelector('.chip');
            if (firstChip) firstChip.focus();
        }, 100);
    }

    renderCurrentQuestion() {
        const question = this.questions[this.currentQuestionIndex];
        if (!question) return;

        // Create question HTML structure
        const questionHTML = `
            <div class="question" data-question-id="${question.id}">
                <h2 class="question-title">${question.title}</h2>
                
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

        if (this.elements.questionContainer) {
            this.elements.questionContainer.innerHTML = questionHTML;
        }
        
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
            } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                e.preventDefault();
                this.focusNextChip(chipElement);
            } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                e.preventDefault();
                this.focusPrevChip(chipElement);
            } else if (e.key === 'Home') {
                e.preventDefault();
                this.focusFirstChip(chipElement.closest('.chip-grid'));
            } else if (e.key === 'End') {
                e.preventDefault();
                this.focusLastChip(chipElement.closest('.chip-grid'));
            }
        });

        return chipElement;
    }

    bindQuestionEvents(question) {
        const answerInput = document.querySelector(`#answer-${question.id}`);

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
        
        // Add visual feedback
        chipElement.style.transform = 'scale(0.95)';
        setTimeout(() => {
            chipElement.style.transform = '';
        }, 150);
        
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
        
        // Debug logging
        console.log(`Chip "${chip.text}" ${isSelected ? 'deselected' : 'selected'} for question ${questionId}`);
        console.log('Current selections:', this.selectedChips[questionId] || []);
    }

    // Methods moved to end of class with enhancements

    updateAnswerInput(questionId) {
        const answerInput = document.querySelector(`#answer-${questionId}`);
        if (!answerInput) return;

        // Don't override if user is manually editing
        if (answerInput.getAttribute('data-manual-edit') === 'true') return;

        const selectedChips = this.selectedChips[questionId] || [];
        const currentValue = answerInput.value.trim();
        
        // Get ALL available chip texts for this question to properly filter custom text
        const question = this.questions.find(q => q.id === questionId);
        const allAvailableChipTexts = question ? question.chipData.map(chip => chip.text) : [];
        
        // Extract custom text that's not from any chip (selected or unselected)
        const customTexts = this.extractCustomText(currentValue, allAvailableChipTexts);
        
        // Combine only selected chips and custom text
        const selectedChipTexts = selectedChips.filter(text => text.trim().length > 0);
        const allTexts = [...selectedChipTexts, ...customTexts];
        
        // Remove duplicates (case-insensitive)
        const uniqueTexts = allTexts.filter((text, index) => {
            if (!text || text.trim().length === 0) return false;
            const lowerText = text.toLowerCase();
            return allTexts.findIndex(t => t.toLowerCase() === lowerText) === index;
        });
        
        const finalText = uniqueTexts.join(', ');
        answerInput.value = finalText;
        this.answers[questionId] = finalText;
        
        // Debug logging
        console.log(`Updated answer input for ${questionId}:`, {
            selectedChips: selectedChips,
            customTexts: customTexts,
            finalText: finalText
        });
    }

    extractCustomText(currentValue, chipTexts) {
        if (!currentValue) return [];
        
        // Split by comma and filter out chip texts (case-insensitive)
        const parts = currentValue.split(',').map(part => part.trim());
        const chipTextsLower = chipTexts.map(text => text.toLowerCase());
        
        // Filter out empty parts and any text that matches available chip texts
        return parts.filter(part => 
            part.length > 0 && 
            !chipTextsLower.includes(part.toLowerCase())
        );
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
        
        // Debug logging
        console.log(`Restored state for question ${question.id}:`, {
            answer: this.answers[question.id],
            selectedChips: this.selectedChips[question.id] || []
        });
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

        // Update button states with null checks
        if (this.elements.prevBtn) {
            this.elements.prevBtn.disabled = isFirstQuestion;
        }
        
        if (this.elements.nextBtn) {
            this.elements.nextBtn.style.display = isLastQuestion ? 'none' : 'inline-flex';
        }
        
        if (this.elements.submitBtn) {
            this.elements.submitBtn.style.display = isLastQuestion ? 'inline-flex' : 'none';
        }
        
        // Enable next/submit only if current question is valid
        if (isLastQuestion) {
            if (this.elements.submitBtn) {
                this.elements.submitBtn.disabled = !hasValidAnswer || !this.allRequiredAnswered();
            }
        } else {
            if (this.elements.nextBtn) {
                this.elements.nextBtn.disabled = !hasValidAnswer;
            }
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
        
        // Null checks to prevent DOM reference errors
        if (this.elements.progressFill) {
            this.elements.progressFill.style.width = `${progress}%`;
        }
        
        if (this.elements.currentQuestion) {
            this.elements.currentQuestion.textContent = this.currentQuestionIndex + 1;
        }
        
        if (this.elements.totalQuestions) {
            this.elements.totalQuestions.textContent = this.totalQuestions;
        }
    }

    handleKeyNavigation(e) {
        // Global keyboard shortcuts
        if (e.altKey || e.ctrlKey || e.metaKey) return;

        switch (e.key) {
            case 'ArrowLeft':
                if (document.activeElement.tagName !== 'INPUT' && 
                    document.activeElement.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    if (this.elements.prevBtn && !this.elements.prevBtn.disabled) {
                        this.previousQuestion();
                    }
                }
                break;
            case 'ArrowRight':
                if (document.activeElement.tagName !== 'INPUT' && 
                    document.activeElement.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    if (this.elements.nextBtn && !this.elements.nextBtn.disabled && this.elements.nextBtn.style.display !== 'none') {
                        this.nextQuestion();
                    } else if (this.elements.submitBtn && !this.elements.submitBtn.disabled && this.elements.submitBtn.style.display !== 'none') {
                        this.submitQuestionnaire();
                    }
                }
                break;
            case 'Escape':
                // Close any modals or return to previous state
                if (this.elements.errorMessage && this.elements.errorMessage.classList.contains('active')) {
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
            // Prepare API request data with correct field mapping
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
            
            // Debug log to see what's being sent
            console.log('API Request Data:', requestData);
            
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
                    reaction: 'They might smile and flip through it immediately, pointing out their favorite photos.',
                    image_search_terms: 'photo album personalized custom',
                    amazon_search_query: 'personalized photo album custom book',
                    price_range: '₹800-2,500'
                },
                {
                    title: 'premium coffee subscription',
                    description: 'Monthly delivery of specialty coffee beans from around the world. Great for coffee lovers who enjoy trying new flavors.',
                    starter: 'You could mention: "I got you a coffee subscription so you can try beans from different countries."',
                    reaction: 'They might get excited about trying new flavors and ask which countries are included.',
                    image_search_terms: 'coffee beans subscription premium',
                    amazon_search_query: 'coffee subscription premium beans delivery',
                    price_range: '₹1,500-4,000/month'
                },
                {
                    title: 'wireless noise-canceling headphones',
                    description: 'High-quality headphones perfect for music lovers or anyone who needs to focus in noisy environments.',
                    starter: 'You could say: "These headphones should help you focus better when things get noisy."',
                    reaction: 'They might immediately want to test them out and ask about the noise-canceling features.',
                    image_search_terms: 'wireless headphones noise canceling',
                    amazon_search_query: 'wireless noise canceling headphones',
                    price_range: '₹5,000-15,000'
                }
            ];
            
            this.renderGiftCards(mockGifts);
        }
    }

    renderGiftCards(gifts) {
        // Use the gift reveal system instead of direct rendering
        if (typeof giftRevealSystem !== 'undefined') {
            giftRevealSystem.setGiftData(gifts);
            giftRevealSystem.renderGiftBoxes();
        } else {
            // Fallback to direct rendering if gift reveal system is not available
            const cardsHTML = gifts.map(gift => `
                <div class="gift-card">
                    <div class="gift-image-container">
                        <img src="https://via.placeholder.com/200x150/ff6600/ffffff?text=Loading..." 
                             alt="${gift.title}" 
                             class="gift-image" 
                             data-search-terms="${gift.image_search_terms || ''}" 
                             onerror="this.src='https://via.placeholder.com/200x150/e2e8f0/4a5568?text=No+Image'">
                    </div>
                    <h3 class="gift-card-title">${gift.title}</h3>
                    <p class="gift-card-description">${gift.description}</p>
                    ${gift.price_range ? `<div class="gift-price">${gift.price_range}</div>` : ''}
                    ${gift.starter ? `<div class="gift-card-starter"><strong>How to present it:</strong> ${gift.starter}</div>` : ''}
                    ${gift.reaction ? `<div class="gift-card-reaction"><strong>Expected reaction:</strong> ${gift.reaction}</div>` : ''}
                    <div class="gift-actions">
                        <a href="https://www.amazon.in/s?k=${encodeURIComponent(gift.amazon_search_query || gift.title)}" 
                           target="_blank" 
                           rel="noopener noreferrer" 
                           class="amazon-btn">
                            <i class="ph ph-shopping-cart"></i>
                            <span>Find on Amazon</span>
                        </a>
                    </div>
                </div>
            `).join('');
            
            this.elements.giftCards.innerHTML = cardsHTML;
        }
    }

    showLoading() {
        if (this.elements.loading) {
            this.elements.loading.classList.add('active');
        }
        document.body.style.overflow = 'hidden';
    }

    hideLoading() {
        if (this.elements.loading) {
            this.elements.loading.classList.remove('active');
        }
        document.body.style.overflow = '';
    }

    showResults() {
        if (this.elements.questionnaire) {
            this.elements.questionnaire.classList.remove('active');
        }
        
        if (this.elements.results) {
            this.elements.results.classList.add('active');
        }
        
        // Announce to screen readers
        this.announceToScreenReader('Gift recommendations loaded successfully');
    }

    showError(message) {
        const errorText = document.getElementById('error-text');
        if (errorText) {
            errorText.textContent = message;
        }
        
        if (this.elements.errorMessage) {
            this.elements.errorMessage.classList.add('active');
        }
        
        document.body.style.overflow = 'hidden';
        
        // Focus error dialog for accessibility
        setTimeout(() => {
            if (this.elements.errorRetryBtn) {
                this.elements.errorRetryBtn.focus();
            }
        }, 100);
    }

    hideError() {
        if (this.elements.errorMessage) {
            this.elements.errorMessage.classList.remove('active');
        }
        document.body.style.overflow = '';
    }

    resetQuestionnaire() {
        // Reset state
        this.currentQuestionIndex = 0;
        this.answers = {};
        this.selectedChips = {};
        
        // Return to landing page
        if (this.elements.results) {
            this.elements.results.classList.remove('active');
        }
        
        if (this.elements.questionnaire) {
            this.elements.questionnaire.classList.remove('active');
        }
        
        if (this.elements.landing) {
            this.elements.landing.classList.add('active');
        }
        
        // Remove fixed navigation class from progress bar
        const progressContainer = document.querySelector('.progress-container');
        if (progressContainer) {
            progressContainer.classList.remove('fixed-nav');
        }
        
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

    // Test function to skip questionnaire and generate gifts with sample data
    async testGiftGeneration() {
        // Fill sample answers with correct API field names
        this.answers = {
            call_them: 'buddy',
            relationship: 'best friend',
            previous_gifts: 'books, coffee mug, funny t-shirt',
            hate: 'loud noises, spicy food, horror movies',
            complaints: 'traffic, work stress, bad weather',
            complain_about_them: 'always running late, too many meetings',
            budget: '₹500-1500',
            limitations: 'no allergies, eco-friendly preferred'
        };
        
        // Show loading immediately
        this.showLoading();
        
        try {
            // Generate gifts with sample data
            await this.generateGiftIdeas();
            this.showResults();
        } catch (error) {
            console.error('Error generating test gifts:', error);
            this.showError('Failed to generate gift ideas. Please try again.');
        } finally {
            this.hideLoading();
        }
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

        // Update selected chips to match textarea content - preserve original case from chip data
        this.selectedChips[questionId] = matchingChips.map(chipText => {
            const originalChip = question.chipData.find(chip => 
                chip.text.toLowerCase() === chipText.toLowerCase()
            );
            return originalChip ? originalChip.text : chipText;
        });
        
        this.updateChipVisualStates(questionId);
        
        // Debug logging
        console.log(`Synced textarea to chips for ${questionId}:`, {
            textareaValue: textareaValue,
            textItems: textItems,
            matchingChips: this.selectedChips[questionId]
        });
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

    // Keyboard navigation helpers
    focusNextChip(currentChip) {
        if (!currentChip) return;
        
        const chipGrid = currentChip.closest('.chip-grid');
        if (!chipGrid) return;
        
        const chips = Array.from(chipGrid.querySelectorAll('.chip'));
        if (chips.length === 0) return;
        
        const currentIndex = chips.indexOf(currentChip);
        const nextIndex = currentIndex < chips.length - 1 ? currentIndex + 1 : 0;
        
        if (chips[nextIndex]) {
            chips[nextIndex].focus();
        }
    }

    focusPrevChip(currentChip) {
        if (!currentChip) return;
        
        const chipGrid = currentChip.closest('.chip-grid');
        if (!chipGrid) return;
        
        const chips = Array.from(chipGrid.querySelectorAll('.chip'));
        if (chips.length === 0) return;
        
        const currentIndex = chips.indexOf(currentChip);
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : chips.length - 1;
        
        if (chips[prevIndex]) {
            chips[prevIndex].focus();
        }
    }

    focusFirstChip(chipGrid) {
        if (!chipGrid) return;
        
        const firstChip = chipGrid.querySelector('.chip');
        if (firstChip) {
            firstChip.focus();
        }
    }

    focusLastChip(chipGrid) {
        if (!chipGrid) return;
        
        const chips = chipGrid.querySelectorAll('.chip');
        if (chips.length > 0) {
            chips[chips.length - 1].focus();
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