/**
 * app.js
 *
 * Lógica general de la interfaz de usuario para la aplicación.
 * Incluye funcionalidades como los botones para limpiar campos de texto.
 */

document.addEventListener('DOMContentLoaded', function() {
    /**
     * Funcionalidad para los botones de limpiar ('X') en los campos de texto.
     *
     * Busca todos los botones con la clase '.clear-input-btn'.
     * Al hacer clic, borra el contenido del campo de texto (<input> o <textarea>)
     * que se encuentra justo antes del botón dentro del mismo contenedor.
     * También gestiona la visibilidad del botón: solo se muestra si el campo tiene texto.
     */
    const clearableInputWrappers = document.querySelectorAll('.input-wrapper');

    clearableInputWrappers.forEach(wrapper => {
        const inputField = wrapper.querySelector('input, textarea');
        const clearButton = wrapper.querySelector('.clear-input-btn');

        if (inputField && clearButton) {
            // Función para actualizar la visibilidad del botón
            const updateButtonVisibility = () => {
                wrapper.classList.toggle('has-content', inputField.value !== '');
            };

            // Evento para limpiar el campo al hacer clic en el botón
            clearButton.addEventListener('click', () => {
                inputField.value = '';
                updateButtonVisibility();
                inputField.focus(); // Devuelve el foco al campo
            });

            // Evento para mostrar/ocultar el botón mientras se escribe
            inputField.addEventListener('input', updateButtonVisibility);

            // Comprobar el estado inicial al cargar la página
            updateButtonVisibility();
        }
    });
});