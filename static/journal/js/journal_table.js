// Функция для получения CSRF из куки (стандарт для Django)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


document.addEventListener('DOMContentLoaded', function() {
    const csrftoken = getCookie('csrftoken');

    // Находим таблицу и берем из неё правильный URL
    const table = document.getElementById('attendance-table');
    const updateUrl = table.dataset.url;

    document.querySelectorAll('.journal-cell').forEach(cell => {
        cell.addEventListener('click', function() {
            const label = this.querySelector('.nb-label');
            const studentId = this.dataset.student;
            const lessonId = this.dataset.lesson;
            const isAbsent = !label.classList.contains('active');

            label.classList.toggle('active');
            this.classList.toggle('has-nb');

            // Теперь используем updateUrl
            fetch(updateUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    'student_id': studentId,
                    'lesson_id': lessonId,
                    'is_absent': isAbsent
                })
            })
            .then(response => {
                if (!response.ok) throw new Error();
            })
            .catch(error => {
                label.classList.toggle('active');
                this.classList.toggle('has-nb');
                alert('Ошибка сохранения');
            });
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // 1. Автоматический расчет итога
    const rows = document.querySelectorAll('tbody tr');

    rows.forEach(row => {
        const inputs = row.querySelectorAll('.grade-input');
        const totalSpan = row.querySelector('.fw-bold.text-success, .fw-bold.text-secondary');

        inputs.forEach(input => {
            input.addEventListener('input', () => {
                let m1 = parseFloat(row.querySelector('input[name^="m1_"]').value) || 0;
                let m2 = parseFloat(row.querySelector('input[name^="m2_"]').value) || 0;
                let final = parseFloat(row.querySelector('input[name^="final_"]').value) || 0;

                // Твоя формула: (M1 + M2 + Final)
                let total = m1 + m2 + final;
                totalSpan.textContent = total.toFixed(1);

                // Меняем цвет если порог пройден (например, 50 баллов)
                if (total >= 50) {
                    totalSpan.classList.replace('text-secondary', 'text-success');
                } else {
                    totalSpan.classList.replace('text-success', 'text-secondary');
                }
            });
        });
    });

    // 2. Удобство: закрытие алертов через 3 секунды
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 3000);
    });
});

