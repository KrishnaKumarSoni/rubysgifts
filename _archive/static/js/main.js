// Ruby's Gifts - Main JavaScript File
// Handles navigation, state management, and common functionality

// Global state management
const AppState = {
    currentPage: 'landing',
    answers: {},
    
    // Save answers to sessionStorage
    saveAnswers() {
        sessionStorage.setItem('giftAnswers', JSON.stringify(this.answers));
    },
    
    // Load answers from sessionStorage
    loadAnswers() {
        const stored = sessionStorage.getItem('giftAnswers');
        if (stored) {
            this.answers = JSON.parse(stored);
        }
    },
    
    // Clear all data
    clear() {
        this.answers = {};
        sessionStorage.removeItem('giftAnswers');
    }
};

// Initialize app state on page load
document.addEventListener('DOMContentLoaded', () => {
    AppState.loadAnswers();
    initializePage();
});

// Initialize page-specific functionality
function initializePage() {
    const path = window.location.pathname;
    
    if (path === '/') {
        AppState.currentPage = 'landing';
        initializeLanding();
    } else if (path === '/questionnaire') {
        AppState.currentPage = 'questionnaire';
        initializeQuestionnaire();
    } else if (path === '/results') {
        AppState.currentPage = 'results';
        initializeResults();
    }
}

// Landing page initialization
function initializeLanding() {
    // Clear any existing data when returning to landing
    AppState.clear();
    
    // Add smooth scrolling for any internal links
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(link.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// Questionnaire page initialization
function initializeQuestionnaire() {
    // This will be implemented when questionnaire page is created
    console.log('Questionnaire page initialized');
}

// Results page initialization
function initializeResults() {
    // Check if we have answers, if not redirect to landing
    if (Object.keys(AppState.answers).length === 0) {
        console.log('No answers found, redirecting to landing');
        window.location.href = '/';
        return;
    }
    
    console.log('Results page initialized with answers:', AppState.answers);
}

// Navigation utilities
const Navigation = {
    // Navigate to a specific page
    goTo(page) {
        if (page === 'questionnaire' && AppState.currentPage === 'landing') {
            // Save current state before navigating
            AppState.saveAnswers();
        }
        
        window.location.href = `/${page === 'landing' ? '' : page}`;
    },
    
    // Navigate back to previous page
    goBack() {
        window.history.back();
    },
    
    // Navigate to results with answers
    goToResults(answers) {
        AppState.answers = answers;
        AppState.saveAnswers();
        this.goTo('results');
    }
};

// Utility functions
const Utils = {
    // Debounce function for search inputs
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Format text for display
    formatText(text) {
        if (!text) return '';
        return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
    },
    
    // Validate form data
    validateAnswers(answers) {
        const required = ['relationship', 'nickname'];
        const missing = required.filter(key => !answers[key] || !answers[key].trim());
        
        if (missing.length > 0) {
            throw new Error(`Missing required fields: ${missing.join(', ')}`);
        }
        
        return true;
    },
    
    // Show notification toast
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        // Remove after delay
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, 3000);
    },
    
    // Copy text to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copied to clipboard!', 'success');
            return true;
        } catch (err) {
            console.error('Failed to copy text: ', err);
            this.showToast('Failed to copy text', 'error');
            return false;
        }
    },
    
    // Generate shareable text for gift ideas
    generateShareText(gift) {
        return `Gift Idea: ${gift.title}\n\n${gift.description}\n\nGenerated by Ruby's Gifts: ${window.location.origin}`;
    },
    
    // Handle errors gracefully
    handleError(error, context = '') {
        console.error(`Error ${context}:`, error);
        
        let message = 'Something went wrong. Please try again.';
        
        if (error.message.includes('fetch')) {
            message = 'Network error. Please check your connection and try again.';
        } else if (error.message.includes('API')) {
            message = 'Service temporarily unavailable. Please try again in a moment.';
        }
        
        this.showToast(message, 'error');
    }
};

// Animation utilities
const Animations = {
    // Fade in elements with stagger
    staggerFadeIn(elements, delay = 100) {
        elements.forEach((el, index) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, index * delay);
        });
    },
    
    // Smooth height transition
    smoothHeight(element, newHeight) {
        element.style.transition = 'height 0.3s ease';
        element.style.height = newHeight + 'px';
        
        setTimeout(() => {
            element.style.height = 'auto';
        }, 300);
    },
    
    // Loading animation for buttons
    setButtonLoading(button, loading = true) {
        if (loading) {
            button.classList.add('loading');
            const icon = button.querySelector('i');
            if (icon) {
                icon.className = 'ph ph-spinner';
            }
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }
};

// Keyboard navigation utilities
const KeyboardNav = {
    // Handle escape key to close modals/go back
    init() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.handleEscape();
            }
        });
    },
    
    handleEscape() {
        // Close any open modals or return to previous step
        const modals = document.querySelectorAll('.modal.open');
        if (modals.length > 0) {
            modals.forEach(modal => modal.classList.remove('open'));
        }
    },
    
    // Make element focusable and add enter key handler
    makeFocusable(element, callback) {
        element.tabIndex = 0;
        element.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                callback(e);
            }
        });
    }
};

// Initialize keyboard navigation
document.addEventListener('DOMContentLoaded', () => {
    KeyboardNav.init();
});

// API utilities
const API = {
    // Base fetch wrapper with error handling
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            Utils.handleError(error, 'making API request');
            throw error;
        }
    },
    
    // Generate gifts from answers
    async generateGifts(answers) {
        return this.request('/generate_gifts', {
            method: 'POST',
            body: JSON.stringify({ answers })
        });
    }
};

// Local storage utilities
const Storage = {
    // Save gift ideas for later
    saveGift(gift) {
        const savedGifts = this.getSavedGifts();
        const giftWithDate = {
            ...gift,
            savedAt: new Date().toISOString(),
            id: Date.now().toString()
        };
        
        savedGifts.push(giftWithDate);
        localStorage.setItem('savedGifts', JSON.stringify(savedGifts));
        
        Utils.showToast('Gift idea saved!', 'success');
        return giftWithDate.id;
    },
    
    // Get all saved gifts
    getSavedGifts() {
        const saved = localStorage.getItem('savedGifts');
        return saved ? JSON.parse(saved) : [];
    },
    
    // Remove a saved gift
    removeSavedGift(id) {
        const savedGifts = this.getSavedGifts();
        const filtered = savedGifts.filter(gift => gift.id !== id);
        localStorage.setItem('savedGifts', JSON.stringify(filtered));
        
        Utils.showToast('Gift idea removed', 'info');
    },
    
    // Clear all saved gifts
    clearSavedGifts() {
        localStorage.removeItem('savedGifts');
        Utils.showToast('All saved gifts cleared', 'info');
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AppState,
        Navigation,
        Utils,
        Animations,
        KeyboardNav,
        API,
        Storage
    };
}

// Make available globally
window.RubyGifts = {
    AppState,
    Navigation,
    Utils,
    Animations,
    KeyboardNav,
    API,
    Storage
};