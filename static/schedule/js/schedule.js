document.addEventListener('DOMContentLoaded', function() {
    const daySelect = document.getElementById('daySelect');

    if (daySelect) {
        daySelect.addEventListener('change', function() {
            const selectedDay = this.value;
            document.querySelectorAll('.day-wrapper').forEach(wrapper => {
                wrapper.style.display = 'none';
            });
            const targetDay = document.getElementById('day-' + selectedDay);
            if (targetDay) {
                targetDay.style.display = 'block';
            }
        });
    }

    const now = new Date();
    let dayOfWeek = now.getDay();
    if (dayOfWeek === 0) dayOfWeek = 7;

    const currentTime = now.getHours().toString().padStart(2, '0') + ":" +
                        now.getMinutes().toString().padStart(2, '0');

    if (daySelect) {
        daySelect.value = dayOfWeek;
        daySelect.dispatchEvent(new Event('change'));
    }

    const currentDayWrapper = document.getElementById(`day-${dayOfWeek}`);
    if (currentDayWrapper) {
        const lessons = currentDayWrapper.querySelectorAll('.lesson-card'); // У тебя в HTML .lesson-card
        lessons.forEach(lesson => {
            const start = lesson.dataset.start;
            const end = lesson.dataset.end;

            if (start && end && currentTime >= start && currentTime <= end) {
                lesson.classList.add('current-lesson');
            }
        });
    }
});