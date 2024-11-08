// Rating system functionality
class RatingSystem {
    constructor() {
        this.initializeRatings();
    }

    initializeRatings() {
        document.querySelectorAll('.rating-input').forEach(container => {
            this.createStarRating(container);
        });
    }

    createStarRating(container) {
        const ratingValue = container.querySelector('input[type="hidden"]');
        const starsContainer = document.createElement('div');
        starsContainer.className = 'stars-container d-flex gap-1';

        for (let i = 1; i <= 5; i++) {
            const star = document.createElement('i');
            star.dataset.value = i;
            star.className = 'star';
            star.setAttribute('data-feather', 'star');
            
            if (i <= parseInt(ratingValue.value)) {
                star.classList.add('active');
            }

            star.addEventListener('click', () => this.handleStarClick(star, ratingValue));
            star.addEventListener('mouseover', () => this.handleStarHover(star));
            star.addEventListener('mouseout', () => this.handleStarOut(star, ratingValue));
            
            starsContainer.appendChild(star);
        }

        container.appendChild(starsContainer);
        feather.replace();
    }

    handleStarClick(star, input) {
        const value = star.dataset.value;
        input.value = value;
        this.updateStars(star.parentElement, value);
    }

    handleStarHover(star) {
        const value = star.dataset.value;
        this.updateStars(star.parentElement, value, true);
    }

    handleStarOut(star, input) {
        this.updateStars(star.parentElement, input.value);
    }

    updateStars(container, value, isHover = false) {
        container.querySelectorAll('.star').forEach(star => {
            const starValue = parseInt(star.dataset.value);
            if (starValue <= value) {
                star.classList.add('active');
            } else {
                star.classList.remove('active');
            }
        });
    }
}

// Initialize rating system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new RatingSystem();
});
