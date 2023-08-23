document.addEventListener('DOMContentLoaded', (event) => {
    const keywordVoteForm = document.querySelector('.keyword-vote-form');
    const voteButtons = document.querySelectorAll('.keyword-vote-btn');
    const voteInput = document.getElementById('keyword_vote');
    const keywordUserVote = document.getElementById('keyword_user_vote');
    const keyword = window.keyword;

    voteButtons.forEach((button) => {
        button.addEventListener('click', (event) => {
            event.preventDefault();

            let voteValue;
            switch (event.target.id) {
                case 'keyword_approve':
                    voteValue = 1;
                    break;
                case 'keyword_reject':
                    voteValue = -1;
                    break;
                case 'keyword_no_vote':
                    voteValue = 0;
                    break;
            }

            voteInput.value = voteValue;

            $.ajax({
                url: voteUrl,
                type: 'POST',
                data: $(keywordVoteForm).serialize(),
                success: function(json) {
                    console.log(json);

                    // Update user vote display
                     keywordUserVote.textContent = json.user_vote;
                     keywordUserVote.className = json.user_vote.toLowerCase();

                    // Redirect to answer_binary page with tailored feedback
                    window.location.href = `/keyword_results/${keyword}/?user_vote=${json.user_vote}`;
                },
                error: function(xhr, errmsg, err) {
                    console.log(xhr.status + ': ' + xhr.responseText);
                }
            });
        });
    });
});
