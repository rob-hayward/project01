import { updatePieChart } from './binary_pie_chart.js';

function toggleSection(event) {
    var section = document.getElementById(event.target.dataset.toggleSection);
    if (section.style.display === "none") {
        section.style.display = "block";
    } else {
        section.style.display = "none";
    }
}

document.addEventListener('DOMContentLoaded', (event) => {
    document.getElementById('change_answer').addEventListener('click', changeAnswer);
    document.getElementById('discuss_edit').addEventListener('click', discussEdit);
    document.getElementById('return_to_tree').addEventListener('click', returnToTree);

    document.querySelectorAll('a[data-word], span[data-word]').forEach((element) => {
        element.addEventListener('click', (event) => {
            let word = event.target.getAttribute('data-word');
            const status = event.target.className.split(' ')[1]; // This assumes the status is always the second class
            if (status === undefined) {
                event.preventDefault();
                const input = document.querySelector('#id_word');
                if (input) {
                    input.value = word.charAt(0).toUpperCase() + word.slice(1);
                }
            }
        });
    });

    const toggleButtons = document.querySelectorAll('button[data-toggle-section]');
    toggleButtons.forEach(button => {
        button.addEventListener('click', toggleSection);
    });

    renderInitialPieCharts();
});

function changeAnswer() {
    let keyword = window.keyword;
    window.location.href = '/keyword_detail/' + keyword + '/';
}

function discussEdit() {
    let keyword = window.keyword;
    window.location.href = '/keyword_discussion/' + keyword + '/';
}

function returnToTree() {
    window.location.href = '/question_tree/';
}

function renderInitialPieCharts() {
    const approveElem = document.querySelector('#keyword_total_approve_votes');
    const rejectElem = document.querySelector('#keyword_total_reject_votes');
    const percentageElem = document.querySelector('#keyword_approval_percentage');

    if(approveElem && rejectElem && percentageElem) {
        let keyword_total_approve_votes = parseInt(approveElem.textContent);
        let keyword_total_reject_votes = parseInt(rejectElem.textContent);
        let keyword_approval_percentage = parseFloat(percentageElem.textContent);
        updatePieChart(keyword_total_approve_votes, keyword_total_reject_votes, keyword_approval_percentage, 100 - keyword_approval_percentage, 'keyword-pie-chart');
    }
}
