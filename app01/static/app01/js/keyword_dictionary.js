function toggleSection(event) {
    var section = document.getElementById(event.target.dataset.toggleSection);
    if (section.style.display === "none") {
        section.style.display = "block";
    } else {
        section.style.display = "none";
    }
}

document.addEventListener('DOMContentLoaded', (event) => {
        document.querySelectorAll('a[data-word], span[data-word]').forEach((element) => {
            element.addEventListener('click', (event) => {
                let word = event.target.getAttribute('data-word');
                const status = event.target.className.split(' ')[1]; // This assumes the status is always the second class

                if (status === undefined) {
                    event.preventDefault();
                    const input = document.querySelector('#id_word'); // Replace 'id_word' with your actual input id
                    if (input) {
                        input.value = word.charAt(0).toUpperCase() + word.slice(1);
                    }
                }
            });
        });

        $('#id_keywords').select2({
            placeholder: 'Select keywords',
            allowClear: true,
        }).on('change', function() {
            var selectedOptions = $('#id_keywords').select2('data');
            var selectedKeywords = selectedOptions.map(function(option) { return option.text; }).join(', ');
            $('#question_tag').val(selectedKeywords);
        });

        const toggleButtons = document.querySelectorAll('button[data-toggle-section]');
        toggleButtons.forEach(button => {
            button.addEventListener('click', toggleSection);
        });
});
