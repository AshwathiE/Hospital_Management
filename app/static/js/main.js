// main.js - Hospital Appointment System Frontend Helpers

document.addEventListener('DOMContentLoaded', () => {
    console.log('Hospital Appointment System Initialized');
    
    // Highlight active nav link based on current path
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // AI Appointment Scheduler Live check
    const doctorSelect = document.querySelector('select[name="doctor_id"]');
    const dateInput = document.querySelector('input[name="appointment_date"]');
    const timeInput = document.querySelector('input[name="appointment_time"]');
    
    const container = document.getElementById('ai-suggestion-container');
    const card = document.getElementById('ai-suggestion-card');
    const title = document.getElementById('ai-suggestion-title');
    const msg = document.getElementById('ai-suggestion-msg');
    const btnContainer = document.getElementById('ai-action-btn-container');
    const applyBtn = document.getElementById('apply-ai-btn');
    const statusEmoji = document.getElementById('ai-status-emoji');

    let suggestedDate = '';
    let suggestedTime = '';

    if (doctorSelect && dateInput && timeInput && container) {
        window.checkAvailability = async function() {
            const doctorId = doctorSelect.value;
            const dateVal = dateInput.value;
            const timeVal = timeInput.value;

            if (!doctorId || !dateVal || !timeVal) {
                container.style.display = 'none';
                return;
            }

            // Extract appointment ID if we are editing
            const form = document.querySelector('form[action*="/edit"]');
            let appointmentId = null;
            if (form) {
                const match = form.getAttribute('action').match(/\/appointments\/([a-f0-9-]+)\/edit/i);
                if (match) {
                    appointmentId = match[1];
                }
            }

            // Show checking status with subtle animation
            container.style.display = 'block';
            card.style.borderColor = 'rgba(14, 165, 233, 0.3)';
            card.style.backgroundColor = 'rgba(14, 165, 233, 0.05)';
            statusEmoji.textContent = '🧠';
            title.textContent = 'AI Scheduler: Analyzing...';
            title.style.color = 'var(--text-primary)';
            msg.textContent = 'Checking doctor schedule and optimizing times...';
            btnContainer.style.display = 'none';

            try {
                const response = await fetch('/appointments/suggest-time', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        doctor_id: doctorId,
                        appointment_date: dateVal,
                        appointment_time: timeVal,
                        appointment_id: appointmentId
                    })
                });

                if (!response.ok) {
                    throw new Error('Network error');
                }

                const data = await response.json();

                if (data.available) {
                    // Slot is free! Show success notice
                    card.style.borderColor = 'rgba(16, 185, 129, 0.4)';
                    card.style.backgroundColor = 'rgba(16, 185, 129, 0.08)';
                    statusEmoji.textContent = '✅';
                    title.textContent = 'AI Scheduler: Slot Available!';
                    title.style.color = 'var(--success)';
                    msg.textContent = 'The selected date and time slot is available for booking.';
                    btnContainer.style.display = 'none';
                } else if (data.error) {
                    // Format error
                    card.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                    card.style.backgroundColor = 'rgba(239, 68, 68, 0.08)';
                    statusEmoji.textContent = '❌';
                    title.textContent = 'AI Scheduler: Invalid Input';
                    title.style.color = 'var(--danger)';
                    msg.textContent = data.error;
                    btnContainer.style.display = 'none';
                } else {
                    // Conflict found, show suggested slot
                    suggestedDate = data.suggested_date;
                    suggestedTime = data.suggested_time;

                    card.style.borderColor = 'rgba(245, 158, 11, 0.4)';
                    card.style.backgroundColor = 'rgba(245, 158, 11, 0.08)';
                    statusEmoji.textContent = '⚠️';
                    title.textContent = 'AI Scheduler: Conflict Detected';
                    title.style.color = 'var(--warning)';
                    msg.textContent = data.suggestion_text || `Doctor is already booked. Suggested slot: ${suggestedTime}`;
                    
                    applyBtn.textContent = `Apply AI Suggested Slot: ${suggestedTime}`;
                    btnContainer.style.display = 'block';
                }
            } catch (err) {
                console.error('Error checking availability:', err);
                card.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                card.style.backgroundColor = 'rgba(239, 68, 68, 0.05)';
                statusEmoji.textContent = '❓';
                title.textContent = 'AI Scheduler: Status Offline';
                msg.textContent = 'Could not verify availability. Submit to test.';
                btnContainer.style.display = 'none';
            }
        };

        // Bind events
        doctorSelect.addEventListener('change', checkAvailability);
        dateInput.addEventListener('change', checkAvailability);
        timeInput.addEventListener('change', checkAvailability);

        // Bind apply button click
        applyBtn.addEventListener('click', () => {
            if (suggestedDate && suggestedTime) {
                dateInput.value = suggestedDate;
                timeInput.value = suggestedTime;
                checkAvailability();
            }
        });

        // Trigger initial check if values are already filled
        if (doctorSelect.value && dateInput.value && timeInput.value) {
            checkAvailability();
        }
    }
});
