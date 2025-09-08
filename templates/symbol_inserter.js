document.addEventListener('DOMContentLoaded', function() {
    const formulaInput = document.getElementById('formula-input');
    if (!formulaInput) return; // Salir si no se encuentra el input

    const symbolButtons = document.querySelectorAll('.symbol-btn');

    symbolButtons.forEach(button => {
        button.addEventListener('click', function() {
            const symbol = this.dataset.symbol;
            const startPos = formulaInput.selectionStart;
            const endPos = formulaInput.selectionEnd;
            const currentValue = formulaInput.value;

            // Insertar el símbolo en la posición del cursor
            formulaInput.value = currentValue.substring(0, startPos) + symbol + currentValue.substring(endPos);

            // Mover el cursor a después del símbolo insertado
            formulaInput.focus();
            const newCursorPos = startPos + symbol.length;
            formulaInput.setSelectionRange(newCursorPos, newCursorPos);
        });
    });
});