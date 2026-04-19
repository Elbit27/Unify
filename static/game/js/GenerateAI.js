

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('aiForm');

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault(); // чтобы страница не перезагружалась

            const topic = document.getElementById('topic').value;
            const count = document.getElementById('count').value;
            const loader = document.getElementById('loader');

            form.style.display = 'none';
            loader.style.display = 'block';

            try {
                const response = await fetch('/game/generate_ai/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        topic: topic,
                        count: parseInt(count)
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    checkTaskStatus(data.task_id);

                    const loaderText = document.querySelector('#loader p');
                    if (loaderText) loaderText.innerText = "Нейросеть генерирует вопросы...";

                } else {
                    alert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
                    form.style.display = 'none';
                    loader.style.display = 'flex';
                }
            } catch (error) {
                console.error('Fetch error:', error);
                alert('Ошибка сервера. Попробуйте позже.');
                form.style.display = 'none';
                loader.style.display = 'flex';
            }
        });
    }
});

function checkTaskStatus(taskId) {
    fetch(`/api/task-status/${taskId}/`)
        .then(res => res.json())
        .then(data => {
            if (data.status === 'SUCCESS') {
                window.location.href = `/games/${data.result.game_id}/`; // Перекидываем в игру
            } else if (data.status === 'FAILURE') {
                alert("Ошибка генерации");
            } else {
                // Если еще PROGRESS, проверяем снова через 3 сек
                setTimeout(() => checkTaskStatus(taskId), 3000);
            }
        });
}

// Функция получения куки
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