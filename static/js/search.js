// Search functionality for games and other content
class SearchHandler {
    constructor() {
        this.searchInput = document.querySelector('.search-input');
        this.searchableItems = document.querySelectorAll('.searchable-item');
        this.initializeSearch();
    }

    initializeSearch() {
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.debounce((e) => {
                this.handleSearch(e.target.value);
            }, 300));
        }
    }

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
    }

    handleSearch(searchTerm) {
        searchTerm = searchTerm.toLowerCase().trim();
        
        this.searchableItems.forEach(item => {
            const searchableText = item.dataset.searchContent.toLowerCase();
            const visible = searchableText.includes(searchTerm);
            
            if (visible) {
                item.classList.remove('d-none');
                this.highlightMatch(item, searchTerm);
            } else {
                item.classList.add('d-none');
            }
        });
    }

    highlightMatch(item, searchTerm) {
        if (!searchTerm) {
            item.innerHTML = item.dataset.originalContent || item.innerHTML;
            return;
        }

        if (!item.dataset.originalContent) {
            item.dataset.originalContent = item.innerHTML;
        }

        let content = item.dataset.originalContent;
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        content = content.replace(regex, '<mark>$1</mark>');
        item.innerHTML = content;
    }
}

// Initialize search functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SearchHandler();
});
