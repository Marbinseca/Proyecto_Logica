// Lógica para los botones de símbolos
document.addEventListener('DOMContentLoaded', function() {
    const formulaInput = document.getElementById('formula-input');
    
    // Solo ejecutar si el campo de fórmula existe en la página actual
    if (formulaInput) {
        const symbolButtons = document.querySelectorAll('.symbol-btn');
        
        symbolButtons.forEach(button => {
            button.addEventListener('click', function() {
                const symbol = this.dataset.symbol;
                const currentPos = formulaInput.selectionStart;
                const currentValue = formulaInput.value;
                
                formulaInput.value = currentValue.substring(0, currentPos) + symbol + currentValue.substring(currentPos);
                formulaInput.focus();
                formulaInput.setSelectionRange(currentPos + symbol.length, currentPos + symbol.length);
            });
        });
    }
});