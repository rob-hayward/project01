document.addEventListener('DOMContentLoaded', (event) => {
    const answerVoteForm = document.querySelector('.answer-vote-form');
    const voteButtons = document.querySelectorAll('.answer-vote-btn');
    const voteInput = document.getElementById('answer_vote');
    const answerUserVote = document.getElementById('answer_user_vote');
    const questionTag = window.questionTag;

    voteButtons.forEach((button) => {
        button.addEventListener('click', (event) => {
            event.preventDefault();

            let voteValue;
            switch (event.target.id) {
                case 'answer_approve':
                    voteValue = 1;
                    break;
                case 'answer_reject':
                    voteValue = -1;
                    break;
                case 'answer_no_vote':
                    voteValue = 0;
                    break;
            }

            voteInput.value = voteValue;

            $.ajax({
                url: voteUrl,
                type: 'POST',
                data: $(answerVoteForm).serialize(),
                success: function(json) {
                    console.log(json);

                    // Update user vote display
                     answerUserVote.textContent = json.user_vote;
                     answerUserVote.className = json.user_vote.toLowerCase();

                    // Redirect to answer_binary page with tailored feedback
                    window.location.href = `/answer_binary/${questionTag}/?user_vote=${json.user_vote}`;
                },
                error: function(xhr, errmsg, err) {
                    console.log(xhr.status + ': ' + xhr.responseText);
                }
            });
        });
    });
});
