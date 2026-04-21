// Можно оставить пустым или добавить общие функции для DataTables
$(document).ready(function() {
    // Автоматическая инициализация DataTables для таблиц с классом .datatable
    $('.datatable').DataTable({
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/ru.json'
        }
    });
});
