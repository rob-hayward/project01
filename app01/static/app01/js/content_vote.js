document.addEventListener('DOMContentLoaded', (event) => {
    const questionVoteForm = document.querySelector('.question-vote-form');
    const voteButtons = document.querySelectorAll('.question-vote-btn');
    const voteInput = document.getElementById('question_vote');
    const questionUserVote = document.getElementById('question_user_vote');
    const questionTag = window.questionTag;

    voteButtons.forEach((button) => {
        button.addEventListener('click', (event) => {
            event.preventDefault();

            let voteValue;
            switch (event.target.id) {
                case 'question_approve':
                    voteValue = 1;
                    break;
                case 'question_reject':
                    voteValue = -1;
                    break;
                case 'question_no_vote':
                    voteValue = 0;
                    break;
            }

            voteInput.value = voteValue;

            $.ajax({
                url: voteUrl,
                type: 'POST',
                data: $(questionVoteForm).serialize(),
                success: function(json) {
                    console.log(json);

                    // Update user vote display
                     questionUserVote.textContent = json.user_vote;
                     questionUserVote.className = json.user_vote.toLowerCase();

                    // Redirect to content_vote_results page with tailored feedback
                    window.location.href = `/content_vote_results/${questionTag}/?user_vote=${json.user_vote}`;
                },
                error: function(xhr, errmsg, err) {
                    console.log(xhr.status + ': ' + xhr.responseText);
                }
            });
        });
    });
});
