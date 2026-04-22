document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault(); // Останавливаем стандартный переход

            // 1. Меняем стили кнопок
            tabButtons.forEach(b => {
                b.classList.remove('active', 'btn-primary');
                b.classList.add('btn-outline-primary', 'border-0');
            });
            this.classList.add('active', 'btn-primary');
            this.classList.remove('btn-outline-primary', 'border-0');

            // 2. Переключаем контент (вкладки)
            const targetSelector = this.getAttribute('data-bs-target');
            const targetEl = document.querySelector(targetSelector);

            if (targetEl) {
                // Скрываем все вкладки
                document.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('show', 'active');
                });
                // Показываем нужную
                targetEl.classList.add('show', 'active');
            }
        });
    });
});

function resetGameDirectly(gameId) {
    // 1. Спрашиваем подтверждение, чтобы не сбросить случайно
    if (!confirm("Вы уверены, что хотите принудительно сбросить эту игру? Все активные участники будут возвращены в лобби.")) {
        return;
    }

    // 2. Определяем протокол (ws или wss для https)
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const socketUrl = protocol + window.location.host + '/ws/game/' + gameId + '/';

    // 3. Создаем временное соединение
    const tempSocket = new WebSocket(socketUrl);

    tempSocket.onopen = function() {
        tempSocket.send(JSON.stringify({
            'action': 'reset_game'
        }));

        setTimeout(() => {
            tempSocket.close();
            window.location.reload();
        }, 500);
    };

    tempSocket.onerror = function(err) {
        console.error("Ошибка при попытке сброса:", err);
        alert("Не удалось сбросить игру. Возможно, сервер недоступен.");
    };
}