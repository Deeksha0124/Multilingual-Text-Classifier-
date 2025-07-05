// Zenify - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Mobile Navigation Toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('open');
            
            // Toggle animation for menu icon
            const spans = menuToggle.querySelectorAll('span');
            spans.forEach(span => span.classList.toggle('active'));
        });
    }
    
    // Testimonials Slider
    const testimonialSlider = document.querySelector('.testimonial-slider');
    
    if (testimonialSlider) {
        const testimonials = testimonialSlider.querySelectorAll('.testimonial-card');
        const dots = document.querySelectorAll('.dot');
        const prevButton = document.querySelector('.testimonial-arrow.prev');
        const nextButton = document.querySelector('.testimonial-arrow.next');
        
        let currentIndex = 0;
        
        function showTestimonial(index) {
            // Hide all testimonials
            testimonials.forEach(testimonial => {
                testimonial.classList.remove('active');
            });
            
            // Remove active class from all dots
            dots.forEach(dot => {
                dot.classList.remove('active');
            });
            
            // Show the selected testimonial
            testimonials[index].classList.add('active');
            
            // Add active class to the corresponding dot
            dots[index].classList.add('active');
            
            // Update current index
            currentIndex = index;
        }
        
        // Event listeners for dots
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                showTestimonial(index);
            });
        });
        
        // Event listeners for prev and next buttons
        if (prevButton) {
            prevButton.addEventListener('click', () => {
                let newIndex = currentIndex - 1;
                if (newIndex < 0) {
                    newIndex = testimonials.length - 1;
                }
                showTestimonial(newIndex);
            });
        }
        
        if (nextButton) {
            nextButton.addEventListener('click', () => {
                let newIndex = currentIndex + 1;
                if (newIndex >= testimonials.length) {
                    newIndex = 0;
                }
                showTestimonial(newIndex);
            });
        }
        
        // Auto-advance the testimonial slider every 5 seconds
        setInterval(() => {
            let newIndex = currentIndex + 1;
            if (newIndex >= testimonials.length) {
                newIndex = 0;
            }
            showTestimonial(newIndex);
        }, 5000);
    }
    
    // Survey form validation
    const surveyForm = document.querySelector('.survey-form');
    
    if (surveyForm) {
        surveyForm.addEventListener('submit', function(event) {
            const requiredFields = surveyForm.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                // Check if radio button group is selected
                if (field.type === 'radio') {
                    const name = field.name;
                    const checked = surveyForm.querySelector(`input[name="${name}"]:checked`);
                    
                    if (!checked) {
                        isValid = false;
                        // Find the question label
                        const questionLabel = surveyForm.querySelector(`label[for="${name}"]`);
                        if (questionLabel) {
                            questionLabel.classList.add('error');
                        }
                    }
                } else if (!field.value.trim()) {
                    // Check if other fields are filled
                    isValid = false;
                    field.classList.add('error');
                }
            });
            
            if (!isValid) {
                event.preventDefault();
                alert('Please fill in all required fields');
            }
        });
    }
    
    // Activity completion and rating
    const completeActivityForm = document.getElementById('complete-activity-form');
    
    if (completeActivityForm) {
        const stars = completeActivityForm.querySelectorAll('.star');
        const ratingInput = document.getElementById('rating');
        
        stars.forEach((star, index) => {
            star.addEventListener('click', () => {
                // Update rating value
                const ratingValue = index + 1;
                ratingInput.value = ratingValue;
                
                // Update star display
                stars.forEach((s, i) => {
                    if (i <= index) {
                        s.classList.add('active');
                    } else {
                        s.classList.remove('active');
                    }
                });
            });
        });
        
        completeActivityForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            const activityId = completeActivityForm.dataset.activityId;
            const rating = ratingInput.value;
            
            try {
                const response = await fetch('/complete_activity', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        activity_id: activityId,
                        rating: parseInt(rating)
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Show success message
                    const completionMessage = document.getElementById('completion-message');
                    if (completionMessage) {
                        completionMessage.classList.remove('hidden');
                    }
                    
                    // Replace form with completed badge
                    completeActivityForm.classList.add('hidden');
                    
                    const completedBadge = document.createElement('div');
                    completedBadge.className = 'completed-badge';
                    completedBadge.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                        Completed
                    `;
                    
                    const actionsDiv = document.querySelector('.activity-detail-actions');
                    if (actionsDiv) {
                        actionsDiv.appendChild(completedBadge);
                    }
                    
                    // Reload the page after a short delay to show updated recommendations
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    alert('Error completing activity: ' + data.message);
                }
            } catch (error) {
                console.error('Error completing activity:', error);
                alert('An error occurred while completing the activity');
            }
        });
    }
    
    // Dashboard charts
    const activityChart = document.getElementById('activity-chart');
    
    if (activityChart && window.Chart) {
        const ctx = activityChart.getContext('2d');
        
        // Sample data - in a real application, this would come from the backend
        const data = {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Activities Completed',
                data: [1, 2, 0, 1, 3, 2, 1],
                backgroundColor: 'rgba(93, 138, 168, 0.2)',
                borderColor: 'rgba(93, 138, 168, 1)',
                borderWidth: 2,
                tension: 0.4,
                pointBackgroundColor: 'rgba(93, 138, 168, 1)'
            }]
        };
        
        const config = {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        };
        
        new Chart(ctx, config);
    }
    
    // Category distribution chart
    const categoryChart = document.getElementById('category-chart');
    
    if (categoryChart && window.Chart) {
        const ctx = categoryChart.getContext('2d');
        
        // Sample data
        const data = {
            labels: ['Meditation', 'Exercise', 'Breathing', 'Journaling', 'Nature', 'Creative'],
            datasets: [{
                data: [4, 2, 3, 1, 2, 1],
                backgroundColor: [
                    'rgba(93, 138, 168, 0.7)',   // Primary
                    'rgba(106, 141, 115, 0.7)',  // Secondary
                    'rgba(242, 192, 145, 0.7)',  // Accent
                    'rgba(76, 175, 80, 0.7)',    // Success
                    'rgba(255, 193, 7, 0.7)',    // Warning
                    'rgba(158, 175, 192, 0.7)'   // Neutral
                ],
                borderWidth: 1
            }]
        };
        
        const config = {
            type: 'doughnut',
            data: data,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        };
        
        new Chart(ctx, config);
    }
});