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
    document.getElementById('return_to_tree').addEventListener('click', returnToTree);
    document.getElementById('content_vote').addEventListener('click', contentVote);

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
    let questionTag = window.questionTag;
    window.location.href = '/question/' + questionTag + '/';
}

function contentVote() {
    let questionTag = window.questionTag;
    window.location.href = '/content_vote/' + questionTag + '/';
}

function returnToTree() {
    window.location.href = '/question_tree/';
}

function renderInitialPieCharts() {
    const approveElem = document.querySelector('#answer_total_approve_votes');
    const rejectElem = document.querySelector('#answer_total_reject_votes');
    const percentageElem = document.querySelector('#answer_approval_percentage');

    if(approveElem && rejectElem && percentageElem) {
        let answer_total_approve_votes = parseInt(approveElem.textContent);
        let answer_total_reject_votes = parseInt(rejectElem.textContent);
        let answer_approval_percentage = parseFloat(percentageElem.textContent);
        updatePieChart(answer_total_approve_votes, answer_total_reject_votes, answer_approval_percentage, 100 - answer_approval_percentage, 'answer-pie-chart');
    }
}
