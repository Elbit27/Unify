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