import { updatePieChart } from './binary_pie_chart.js';

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

        function renderInitialPieCharts() {
            let question_tag_total_approve_votes = parseInt(document.querySelector('#question_tag_total_approve_votes').textContent);
            let question_tag_total_reject_votes = parseInt(document.querySelector('#question_tag_total_reject_votes').textContent);
            let question_tag_approval_percentage = parseFloat(document.querySelector('#question_tag_approval_percentage').textContent);
            updatePieChart(question_tag_total_approve_votes, question_tag_total_reject_votes, question_tag_approval_percentage, 100 - question_tag_approval_percentage, 'question-tag-pie-chart');

            let question_total_approve_votes = parseInt(document.querySelector('#question_total_approve_votes').textContent);
            let question_total_reject_votes = parseInt(document.querySelector('#question_total_reject_votes').textContent);
            let question_approval_percentage = parseFloat(document.querySelector('#question_approval_percentage').textContent);
            updatePieChart(question_total_approve_votes, question_total_reject_votes, question_approval_percentage, 100 - question_approval_percentage, 'question-pie-chart');
        }

        function processVote(buttonsSelector, voteInputId, voteFormSelector, voteOutputIds) {
            document.querySelectorAll(buttonsSelector).forEach((element) => {
                element.addEventListener('click', (event) => {
                    event.preventDefault();

                    let voteValue;
                    if (event.target.id.endsWith('_approve')) {
                        voteValue = 1;
                    } else if (event.target.id.endsWith('_reject')) {
                        voteValue = -1;
                    } else {
                        voteValue = 0;
                    }

                    // Set the vote value to the hidden field
                    let voteInput = document.getElementById(voteInputId);
                    voteInput.value = voteValue;

                    $.ajax({
                        url : voteUrl,
                        type : "POST",
                        data : $(voteFormSelector).serialize(),

                        success : function(json) {
                            console.log(json);
                            // Update the vote statistics and status
                            $(voteOutputIds.total_votes).text(json.total_votes);
                            $(voteOutputIds.total_approve_votes).text(json.total_approve_votes);
                            $(voteOutputIds.total_reject_votes).text(json.total_reject_votes);
                            $(voteOutputIds.participation_percentage).text(json.participation_percentage);
                            $(voteOutputIds.approval_percentage).text(json.approval_percentage);
                            $(voteOutputIds.status).text(json.status);
                            $(voteOutputIds.user_vote).text(json.user_vote);

                            // Update the pie charts
                            if (buttonsSelector == ".question-tag-vote-btn") {
                                updatePieChart(json.total_approve_votes, json.total_reject_votes, json.approval_percentage, 100 - json.approval_percentage, 'question-tag-pie-chart');
                            } else if (buttonsSelector == ".question-vote-btn") {
                                updatePieChart(json.total_approve_votes, json.total_reject_votes, json.approval_percentage, 100 - json.approval_percentage, 'question-pie-chart');
                            }

                            // Update the status class
                            $(voteOutputIds.status).removeClass('approved proposed rejected alternative');
                            if (json.status === 'Approved') {
                                $(voteOutputIds.status).addClass('approved');
                            } else if (json.status === 'Proposed') {
                                $(voteOutputIds.status).addClass('proposed');
                            } else if (json.status === 'Rejected') {
                                $(voteOutputIds.status).addClass('rejected');
                            } else if (json.status === 'Alternative') {
                                $(voteOutputIds.status).addClass('alternative');
                            }

                            // Update the user_vote class
                            $(voteOutputIds.user_vote).removeClass('approve reject no-vote');
                            if (json.user_vote == 'Approve') {
                                $(voteOutputIds.user_vote).addClass('approve');
                            } else if (json.user_vote == 'Reject') {
                                $(voteOutputIds.user_vote).addClass('reject');
                            } else {
                                $(voteOutputIds.user_vote).addClass('no-vote');
                            }
                        },

                        error : function(xhr,errmsg,err) {
                            console.log(xhr.status + ": " + xhr.responseText);
                        }
                    });
                });
            });
        }

        renderInitialPieCharts();

        processVote('.question-tag-vote-btn', 'question_tag_vote', '.question-tag-vote-form', {
            total_votes: '#question_tag_total_votes',
            total_approve_votes: '#question_tag_total_approve_votes',
            total_reject_votes: '#question_tag_total_reject_votes',
            participation_percentage: '#question_tag_participation_percentage',
            approval_percentage: '#question_tag_approval_percentage',
            status: '#question_tag_status',
            user_vote: '#question_tag_user_vote',
        });

        processVote('.question-vote-btn', 'question_vote', '.question-vote-form', {
            total_votes: '#question_total_votes',
            total_approve_votes: '#question_total_approve_votes',
            total_reject_votes: '#question_total_reject_votes',
            participation_percentage: '#question_participation_percentage',
            approval_percentage: '#question_approval_percentage',
            status: '#question_status',
            user_vote: '#question_user_vote',
        });
    });