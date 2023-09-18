function discussEdit() {
    let keyword = window.keyword;
    window.location.href = '/keyword_discussion/' + keyword + '/';
}

document.addEventListener('DOMContentLoaded', (event) => {
    const keywordVoteForm = document.querySelector('.keyword-vote-form');
    const voteButtons = document.querySelectorAll('.keyword-vote-btn');
    const voteInput = document.getElementById('keyword_vote');
    const keywordUserVote = document.getElementById('keyword_user_vote');
    const keyword = window.keyword;

    // New Event Listener for 'discuss_edit'
    document.getElementById('discuss_edit').addEventListener('click', discussEdit);

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

                     keywordUserVote.textContent = json.user_vote;
                     keywordUserVote.className = json.user_vote.toLowerCase();

                     window.location.href = `/keyword_results/${keyword}/?user_vote=${json.user_vote}`;
                },
                error: function(xhr, errmsg, err) {
                    console.log(xhr.status + ': ' + xhr.responseText);
                }
            });
        });
    });
});
