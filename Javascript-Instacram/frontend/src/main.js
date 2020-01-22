// importing named exports we use brackets
import { createPostTile, createElement, createLocalPostTile } from './helpers.js';

// when importing 'default' exports, use below syntax
import API from './api.js';

const api  = new API();

var page = 0;
if (localStorage.getItem('AUTH_TOKEN')) {
    window.localStorage.setItem('ROLE', 'feed');
    removePosts();
    page = 0;
    getHomePage();
    getUser();
} else {
    console.log('local');
    getPosts('feed.json');
}

async function getUser() {
    const token = window.localStorage.getItem('AUTH_TOKEN');
    try {
        const response = await fetch('http://127.0.0.1:5000/user',
        {
        method: 'GET',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            Authorization: `token ${token}`
            }
        });
        console.log('status: ', response.status);
        if (response.status == 200) {
            var data = await response.json();
            window.localStorage.setItem('USERID', data.id);
        } else if (response.status == 409) {
            alert('get user fail!');
        }
    } catch (e) {
        console.log('Err',e);
    }
}

document.getElementById('ins').addEventListener('click', function(){
    window.localStorage.removeItem('ROLE');
    window.localStorage.setItem('ROLE', 'feed');
    page = 0;
    removePosts();
    getHomePage();
});
document.getElementById('mypage').addEventListener('click', mypage);
async function mypage(){
    removePosts();
    page = 0;
    window.localStorage.removeItem('ROLE');
    window.localStorage.setItem('ROLE', 'user');
    const token = window.localStorage.getItem('AUTH_TOKEN');
    try {
        const response = await fetch('http://127.0.0.1:5000/user',
        {
        method: 'GET',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            Authorization: `token ${token}`
            }
        });
        console.log('status: ', response.status);
        if (response.status == 200) {
            var data = await response.json();
            var posts = data.posts;
            posts.map(async function (postid) {
                const responsePost = await fetch('http://127.0.0.1:5000/post?id=' + postid,
                {
                method: 'GET',
                headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json',
                    Authorization: `token ${token}`
                    }
                });
                console.log('status: ', responsePost.status);
                if (responsePost.status == 200) {
                    var parent = document.getElementById('large-feed');
                    var post = await responsePost.json();
                    console.log('post: ', post);
                    parent.appendChild(createPostTile(post, 'mypage'));
                    addDeleteEvent(post);
                    addUpdateEvent(post);
                    addLikeModal(parent, post);
                    addCommentModal(parent, post);
                } else if (response.status == 409) {
                    alert('get post fail!');
                }
            });
        } else if (response.status == 409) {
            alert('get user posts fail!');
        }
    } catch (e) {
        console.log('Err',e);
    }
}
// we can use this single api request multiple times
function getPosts(name) {
    var feed = api.getFeed(name);
    feed.then(posts => {
        posts.reduce((parent, post) => {
            parent.appendChild(createLocalPostTile(post));
            return parent;
        }, document.getElementById('large-feed'))
    });
}

function addUserPageEvent(post) {
    var h2El = document.getElementById('h2_' + post.id);
    var imgEl = document.getElementById('img_' + post.id);
    h2El.addEventListener('click', function() {
        removePosts();
        page = 0;
        getHomePage(h2El.textContent);
    });
    imgEl.addEventListener('click', function() {
        removePosts();
        page = 0;
        getHomePage(h2El.textContent);
    });  
}

function addDeleteEvent(post) {
    var del = document.getElementById('delete_' + post.id);
    del.addEventListener('click', async function() {
        const token = window.localStorage.getItem('AUTH_TOKEN');
        try {
            const response = await fetch('http://127.0.0.1:5000/post?id=' + post.id,
            {
              method: 'DELETE',
              headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                Authorization: `token ${token}`
                }
            });
            if (response.status == 200) {
                mypage();
                console.log('delete successfully!');
            } else if (response.status == 409) {
                alert('delete fail!');
            } else if (response.status == 403) {
                alert('delete fail, u cannot delete others post!');
            } else if (response.status == 404) {
                alert('delete fail, post not found!');
            }
        } catch (e) {
            console.log('Err',e);
        }
    });
}

function addUpdateEvent(post) {
    var upd = document.getElementById('update_' + post.id);
    upd.addEventListener('click', function() {
        var modal = document.createElement('modal');
        modal.className = 'modal';
        //modal.style.height = '300px';
        var fileEl = document.createElement('input');
        fileEl.type = 'file';
        var dataURL = '';
        fileEl.addEventListener('change', function(event) {
            const [ file ] = event.target.files;
            const validFileTypes = [ 'image/jpeg', 'image/png', 'image/jpg' ]
            const valid = validFileTypes.find(type => type === file.type);
            // bad data, let's walk away
            if (!valid)
                return false;
            // if we get here we have a valid image
            const reader = new FileReader();
            reader.onload = (e) => {
                // do something with the data result
                dataURL = e.target.result;
                console.log('dataURL: ', dataURL);
                const image = createElement('img', null, { src: dataURL });
                modal.appendChild(image);
            };
            console.log('file: ', file);
            // this returns a base64 image
            reader.readAsDataURL(file);
        });
        modal.appendChild(fileEl);
        var descriptEl = document.createElement('input');
        var time = new Date().getTime();
        descriptEl.id = 'descript_' + time;
        descriptEl.type = 'text';
        var submitBtn = document.createElement('button');
        submitBtn.textContent = 'submit';
        submitBtn.id = 'post_sub';
        var closeEl = document.createElement('span');
        closeEl.className = 'close';
        closeEl.textContent = 'close';
        closeEl.addEventListener('click', function(){
            modal.style.display = 'none';
        });
        modal.appendChild(descriptEl);
        modal.appendChild(submitBtn);
        modal.appendChild(closeEl);
        modal.style.display = 'block';
        document.getElementById('large-feed').appendChild(modal);
        
        submitBtn.addEventListener('click', async function() {
            var descript_str = document.getElementById('descript_' + time).value;
            var imgData = '';
            if (dataURL !== '') {
                imgData = dataURL.split(',')[1];
            }
            const token = window.localStorage.getItem('AUTH_TOKEN');
            try {
                const response = await fetch('http://127.0.0.1:5000/post?id=' + post.id,
                {
                method: 'PUT',
                headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json',
                    Authorization: `token ${token}`
                    },
                    body: JSON.stringify({
                        "description_text": descript_str,
                        "src": imgData
                    })
                });
                if (response.status == 200) {
                    mypage();
                    console.log('update successfully!');
                } else if (response.status == 409) {
                    alert('update fail!');
                } else if (response.status == 403) {
                    alert('update fail, u cannot delete others post!');
                } else if (response.status == 404) {
                    alert('update fail, post not found!');
                }
            } catch (e) {
                console.log('Err',e);
            }
        });
    });
}

function addLikeEvent(post) {
    var like = document.getElementById('l_' + post.id);
    var like_count = post.meta.likes.length;
    like.addEventListener('click', async function() {
        try {
            const token = window.localStorage.getItem('AUTH_TOKEN');
            if (like.textContent === ' like ') {
                const response = await fetch('http://127.0.0.1:5000/post/like?id=' + post.id,
                {
                method: 'PUT',
                headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json',
                    Authorization: `token ${token}`
                    }
                });
                console.log('status: ', response.status);
                if (response.status == 200) {
                    like_count++;
                    var post_like = document.getElementById('like_' + post.id);
                    var modal = document.getElementById('modal_l_' + post.id);
                    var pEl = document.createElement('p');
                    pEl.textContent = localStorage.getItem('USER');
                    modal.appendChild(pEl);
                    post_like.textContent = like_count + ' likes ';
                    like.textContent = ' unlike ';
                } else if (response.status == 409) {
                    alert('put fail!');
                } else if (response.status == 403) {
                    alert('put fail, u have to login first!');
                    Modal.style.display = 'none';
                }
            } else {
                const response = await fetch('http://127.0.0.1:5000/post/unlike?id=' + post.id,
                {
                method: 'PUT',
                headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json',
                    Authorization: `token ${token}`
                    }
                });
                console.log('status: ', response.status);
                if (response.status == 200) {
                    like_count--;
                    var post_like = document.getElementById('like_' + post.id);
                    var modal = document.getElementById('modal_l_' + post.id);
                    modal.lastChild.remove();
                    post_like.textContent = like_count + ' likes ';
                    like.textContent = ' like ';
                    //addLikeModal(parent, post);
                } else if (response.status == 409) {
                    alert('put fail!');
                } else if (response.status == 403) {
                    alert('put fail, u have to login first!');
                    Modal.style.display = 'none';
                }
            }
        } catch (e) {
            console.log('Err',e);
        }
    });
}

function addCommentEvent(parent, post) {
    var comment = document.getElementById('c_' + post.id);
    var Modal = document.createElement('modal');
    Modal.className = 'modal';
    Modal.id = 'modal_c_e_' + post.id;
    Modal.style.display = 'none';
    var commentEl = document.createElement('input');
    var time = new Date().getTime();
    commentEl.id = 'post_comment_' + time;
    commentEl.type = 'text';
    var submitBtn = document.createElement('button');
    submitBtn.textContent = 'submit';
    var closeEl = document.createElement('span');
    closeEl.className = 'close';
    closeEl.textContent = 'close';
    closeEl.addEventListener('click', function(){
        Modal.style.display = 'none';
    });
    Modal.appendChild(commentEl);
    Modal.appendChild(submitBtn);
    Modal.appendChild(closeEl);
    comment.addEventListener('click', function() {
        Modal.style.display = 'block';
    });
    parent.appendChild(Modal);
    submitBtn.addEventListener('click', async function() {
        var comment_str = document.getElementById('post_comment_' + time).value;
        var published_str = new Date();
        var author_str = localStorage.getItem('USER');
        const token = window.localStorage.getItem('AUTH_TOKEN');
        try {
            const response = await fetch('http://127.0.0.1:5000/post/comment?id=' + post.id,
            {
              method: 'PUT',
              headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                Authorization: `token ${token}`
                },
               body: JSON.stringify({
                    "author": author_str,
                    "published": published_str,
                    "comment": comment_str
                })
            });
            if (response.status == 200) {
                var modal = document.getElementById('modal_c_' + post.id);
                var comment_like = document.getElementById('comment_' + post.id);
                var pEl = document.createElement('p');
                var date = published_str;
                pEl.textContent = author_str + ' : ' + comment_str;
                var ptimeEl = document.createElement('p');
                ptimeEl.textContent = 'comment at : ' + date.toISOString().slice(0,10) + ' ' + date.toTimeString().split(' ')[0];
                modal.appendChild(pEl);
                modal.appendChild(ptimeEl);
                comment_like.textContent = (post.comments.length + 1) + ' comments ';
                Modal.style.display = 'none';
            } else if (response.status == 409) {
                alert('put fail!');
            } else if (response.status == 403) {
                alert('put fail, u have to login first!');
                Modal.style.display = 'none';
            }
        } catch (e) {
            console.log('Err',e);
        }
    });
}

function addUnfollowEvent(post) {
    var unfollow = document.getElementById('f_' + post.id);
    unfollow.addEventListener('click', async function() {
        var author_str = post.meta.author;
        const token = window.localStorage.getItem('AUTH_TOKEN');
        if (unfollow.textContent === ' unfollow ') {
            try {
                const response = await fetch('http://127.0.0.1:5000/user/unfollow?username=' + author_str,
                {
                method: 'PUT',
                headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json',
                    Authorization: `token ${token}`
                    }
                });
                if (response.status == 200) {
                    console.log('unfollow sucess!');
                    unfollow.textContent = 'follow';
                    removePosts();
                    page = 0;
                    getHomePage();
                } else if (response.status == 409) {
                    alert('unfollow fail!');
                }
            } catch (e) {
                console.log('Err',e);
            }
        } else {
            const response = await fetch('http://localhost:5000/user/follow?username=' + author_str,
            {
            method: 'PUT',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                Authorization: `token ${token}`
            }
            });
            if (response.status == 200) {
                console.log('follow sucess!');
                unfollow.textContent = 'unfollow';
            } else {
                alert('follow failed');
            }   
        }
    });
}

// Potential example to upload an image
const input = document.querySelector('input[type="file"]');
input.addEventListener('change', uploadImage);
function uploadImage(event) {
    var modal = document.createElement('modal');
    modal.className = 'modal';
    modal.style.height = '300px';
    const [ file ] = event.target.files;
    const validFileTypes = [ 'image/jpeg', 'image/png', 'image/jpg' ]
    const valid = validFileTypes.find(type => type === file.type);
    // bad data, let's walk away
    if (!valid)
        return false;
    // if we get here we have a valid image
    const reader = new FileReader();
    var dataURL;
    reader.onload = (e) => {
        // do something with the data result
        dataURL = e.target.result;
        console.log('dataURL: ', dataURL);
        const image = createElement('img', null, { src: dataURL });
        modal.appendChild(image);
    };
    console.log('file: ', file);
    // this returns a base64 image
    reader.readAsDataURL(file);

    var descriptEl = document.createElement('input');
    var time = new Date().getTime();
    descriptEl.id = 'descript_' + time;
    descriptEl.type = 'text';
    var submitBtn = document.createElement('button');
    submitBtn.textContent = 'submit';
    submitBtn.id = 'post_sub';
    var closeEl = document.createElement('span');
    closeEl.className = 'close';
    closeEl.textContent = 'close';
    closeEl.addEventListener('click', function(){
        modal.style.display = 'none';
    });
    modal.appendChild(descriptEl);
    modal.appendChild(submitBtn);
    modal.appendChild(closeEl);
    modal.style.display = 'block';
    document.getElementById('large-feed').appendChild(modal);
    
    submitBtn.addEventListener('click', async function() {
        var descript_str = document.getElementById('descript_' + time).value;
        console.log(dataURL.split(',')[1]);
        const token = window.localStorage.getItem('AUTH_TOKEN');
        try {
            const response = await fetch('http://127.0.0.1:5000/post',
            {
            method: 'POST',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                Authorization: `token ${token}`
                },
            body: JSON.stringify({
                    "description_text": descript_str,
                    "src": dataURL.split(',')[1]
                })
            });
            console.log('status: ', response.status);
            if (response.status == 200) {
                var data = await response.json();
                console.log('post_id: ', data.post_id);
                modal.style.display = 'none';
                removePosts();
                page = 0;
                getHomePage();
            } else if (response.status == 409) {
                alert('post fail!');
            }
        } catch (e) {
            console.log('Err',e);
        }
    });
    
}


async function addLikeModal(parent, post) {
    var post_like = document.getElementById('like_' + post.id);
    var Modal = document.createElement('modal');
    Modal.className = 'modal';
    Modal.id = 'modal_l_' + post.id;
    Modal.style.display = 'none';
    for (var i = 0; i < post.meta.likes.length; i++) {
        var pEl = document.createElement('p');
        const token = window.localStorage.getItem('AUTH_TOKEN');
        var name = '';
        try {
            const response = await fetch('http://127.0.0.1:5000/user?id=' + post.meta.likes[i],
            {
            method: 'GET',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                Authorization: `token ${token}`
                }
            });
            console.log('status: ', response.status);
            if (response.status == 200) {
                var user = await response.json();
                name = user.username;
                console.log('name: ', name);
                pEl.textContent = name;
            } else if (response.status == 409) {
                alert('get user fail!');
            }
        } catch (e) {
            console.log('Err',e);
        }
        Modal.appendChild(pEl);
    }
    post_like.addEventListener('click', function(){
        if (Modal.style.display === 'none') {
            Modal.style.display = 'block';
        }
    });
    Modal.addEventListener('click', function(){
        Modal.style.display = 'none';
    });
    parent.appendChild(Modal);
}

function addCommentModal(parent, post) {
    var post_com = document.getElementById('comment_' + post.id);
    var Modal = document.createElement('modal');
    Modal.className = 'modal';
    Modal.id = 'modal_c_' + post.id;
    Modal.style.display = 'none';
    for (var i = 0; i < post.comments.length; i++) {
        var pEl = document.createElement('p');
        var date = new Date(post.comments[i].published*1000);
        pEl.textContent = post.comments[i].author + ' : ' + post.comments[i].comment;
        var ptimeEl = document.createElement('p');
        ptimeEl.textContent = 'comment at : ' + date.toISOString().slice(0,10) + ' ' + date.toTimeString().split(' ')[0];
        Modal.appendChild(pEl);
        Modal.appendChild(ptimeEl);
    }
    post_com.addEventListener('click', function(){
        if (Modal.style.display === 'none') {
            Modal.style.display = 'block';
        }
    });
    Modal.addEventListener('click', function(){
        Modal.style.display = 'none';
    });
    parent.appendChild(Modal);
}

function removePosts() {
    var feedEl = document.getElementById('large-feed');
    while (feedEl.hasChildNodes()) {
        var t = feedEl.removeChild(feedEl.lastChild);
    }
}

document.getElementById('followSearch').addEventListener('click', function(){
    if (document.getElementById('followDiv').style.display === 'block') {
        document.getElementById('followDiv').style.display = 'none';
    } else {
        document.getElementById('followDiv').style.display = 'block';
    }
});
document.getElementById('login').addEventListener('click', function(){
    if (document.getElementById('loginDiv').style.display === 'block') {
        document.getElementById('loginDiv').style.display = 'none';
    } else {
        document.getElementById('loginDiv').style.display = 'block';
    }
    document.getElementById('signUpDiv').style.display = 'none';
});
document.getElementById('signUp').addEventListener('click', function(){
    if (document.getElementById('signUpDiv').style.display === 'block') {
        document.getElementById('signUpDiv').style.display = 'none';
    } else {
        document.getElementById('signUpDiv').style.display = 'block';
    }
    document.getElementById('loginDiv').style.display = 'none';
});
document.getElementById('logout').addEventListener('click', function(){
    document.getElementById('signUpDiv').style.display = 'none';
    document.getElementById('loginDiv').style.display = 'none';
    localStorage.clear();
    removePosts();
    getPosts('feed.json');
    page = 0;
});
document.getElementById('profile').addEventListener('click',
    async function() {
        const token = window.localStorage.getItem('AUTH_TOKEN');
        const userName = window.localStorage.getItem('USER');
        const response = await fetch('http://localhost:5000/user?username=' + userName,
        {
        method: 'GET',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            Authorization: `token ${token}`
        }
        });
        if (response.status == 200) {
            var data = await response.json();
            console.log('data', data);
            var Modal = document.createElement('modal');
            Modal.className = 'modal';
            Modal.id = 'modal_c_' + data.id;
            Modal.style.display = 'block';

            var title = document.createElement('p');
            title.className = 'title';
            title.textContent = 'Profile';
            

            var modal_content = document.createElement('div');
            modal_content.className = 'modal-content';
            var closeEl = document.createElement('span');
            closeEl.className = 'close';
            closeEl.textContent = 'Close';
            closeEl.addEventListener('click', function(){
                Modal.style.display = 'none';
            });
            Modal.appendChild(closeEl);
            Modal.appendChild(title);
            modal_content.appendChild(createElement('p', 'username: ' + data.username));
            modal_content.appendChild(createElement('p', 'email: ' + data.email));
            modal_content.appendChild(createElement('p', 'follower: ' + data.followed_num));
            modal_content.appendChild(createElement('p', 'following: ' + data.following.length));
            var followUl = document.createElement('ul');
            for (var f = 0; f < data.following.length; f++) {
                var liEl = document.createElement('li');
                const token = window.localStorage.getItem('AUTH_TOKEN');
                var name = '';
                try {
                    const response = await fetch('http://127.0.0.1:5000/user?id=' + data.following[f],
                    {
                    method: 'GET',
                    headers: {
                        Accept: 'application/json',
                        'Content-Type': 'application/json',
                        Authorization: `token ${token}`
                        }
                    });
                    console.log('status: ', response.status);
                    if (response.status == 200) {
                        var user = await response.json();
                        name = user.username;
                        console.log('name: ', name);
                        liEl.textContent = name;
                    } else if (response.status == 409) {
                        alert('get user fail!');
                    }
                } catch (e) {
                    console.log('Err',e);
                }
                followUl.appendChild(liEl);
            }
            modal_content.appendChild(followUl);
            modal_content.appendChild(createElement('p', 'you have ' + data.posts.length + ' posts'));
            var updateEl = document.createElement('span');
            updateEl.className = 'update';
            updateEl.textContent = 'Edit';
            updateEl.addEventListener('click', async function(){
                Modal.remove();
                var upModal = document.createElement('modal');
                upModal.className = 'modal';
                upModal.id = 'upmodal_c_' + data.id;
                upModal.style.display = 'block';

                var title_up = document.createElement('p');
                title_up.className = 'title';
                title_up.textContent = 'Edit Profile';

                var modal_content_up = document.createElement('div');
                modal_content_up.className = 'modal-content';
                var upcloseEl = document.createElement('span');
                upcloseEl.textContent = 'Close';
                upcloseEl.className = 'close';
                upcloseEl.addEventListener('click', function(){
                    upModal.remove();
                });
                upModal.appendChild(upcloseEl);
                upModal.appendChild(title_up);
                modal_content_up.appendChild(createElement('p', 'name: '));
                modal_content_up.appendChild(createElement('input', null, { placeholder: 'name', value: data.name, id: 'proUpUserName' }));
                modal_content_up.appendChild(createElement('p', 'email: '));
                modal_content_up.appendChild(createElement('input', null, { placeholder: 'email', value: data.email, id: 'proUpEmail' }));
                modal_content_up.appendChild(createElement('p', 'password: '));
                modal_content_up.appendChild(createElement('input', null, { placeholder: 'password', value: '', id: 'proUpPW' }));
                modal_content_up.appendChild(createElement('p', 'follower: ' + data.followed_num));
                modal_content_up.appendChild(createElement('p', 'following: ' + data.following.length));
                var followUl = document.createElement('ul');
                for (var f = 0; f < data.following.length; f++) {
                    var liEl = document.createElement('li');
                    const token = window.localStorage.getItem('AUTH_TOKEN');
                    var name = '';
                    try {
                        const response = await fetch('http://127.0.0.1:5000/user?id=' + data.following[f],
                        {
                        method: 'GET',
                        headers: {
                            Accept: 'application/json',
                            'Content-Type': 'application/json',
                            Authorization: `token ${token}`
                            }
                        });
                        console.log('status: ', response.status);
                        if (response.status == 200) {
                            var user = await response.json();
                            name = user.username;
                            console.log('name: ', name);
                            liEl.textContent = name;
                        } else if (response.status == 409) {
                            alert('get user fail!');
                        }
                    } catch (e) {
                        console.log('Err',e);
                    }
                    followUl.appendChild(liEl);
                }
                modal_content_up.appendChild(followUl);
                modal_content_up.appendChild(createElement('p', 'posts: ' + data.posts.length));

                var updateSubEl = document.createElement('span');
                updateSubEl.textContent = 'submit';
                updateSubEl.className = 'update';
                updateSubEl.addEventListener('click', async function(){
                    const token = window.localStorage.getItem('AUTH_TOKEN');
                    try {
                        const response = await fetch('http://127.0.0.1:5000/user',
                        {
                        method: 'PUT',
                        headers: {
                            Accept: 'application/json',
                            'Content-Type': 'application/json',
                            Authorization: `token ${token}`
                            },
                        body: JSON.stringify({
                                "email": document.getElementById('proUpEmail').value,
                                "name": document.getElementById('proUpUserName').value,
                                "password": document.getElementById('proUpPW').value
                            })
                        });
                        if (response.status == 200) {
                            console.log('update successfully!');
                            upModal.remove();
                        } else if (response.status == 409) {
                            alert('update fail!');
                        } else if (response.status == 403) {
                            alert('update fail, u have to login first!');
                        }
                    } catch (e) {
                        console.log('Err',e);
                    }
                });
                modal_content_up.appendChild(updateSubEl);
                upModal.appendChild(modal_content_up);
                document.getElementById('large-feed').appendChild(upModal);
            });
            modal_content.appendChild(updateEl); 
            Modal.appendChild(modal_content); 
            document.getElementById('large-feed').appendChild(Modal);
        } else {
            alert('cannot get user info!');
        }  
});

document.getElementById('signUpBtn').addEventListener('click', 
    async function() {
        const userName = document.getElementById('Susername').value;
        const userPass = document.getElementById('Suserpass').value;
        const email = document.getElementById('email').value;
        const name = document.getElementById('name').value;
        if (userName == "" || userName == null) {
            alert("Please Enter User Name");
        } else if (userPass == "" || userPass == null) {
            alert("Please Enter Password");
        } else {
            try {
                const response = await fetch('http://127.0.0.1:5000/auth/signup',
                {
                  method: 'POST',
                  headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        "username": userName,
                        "password": userPass,
                        "email": email,
                        "name": name
                    })
                });
                console.log('status: ', response.status);
                if (response.status == 200) {
                    document.getElementById('signUpDiv').style.display = 'none';
                    //follow(userName);
                } else if (response.status == 409) {
                    alert('account already exist!');
                }
            } catch (e) {
                console.log('Err',e);
            }
        }
}); 

document.getElementById('loginBtn').addEventListener('click', 
    async function() {
        getUser();
        const userName = document.getElementById('username').value;
        const userPass = document.getElementById('userpass').value;
        if (userName == "" || userName == null) {
            alert("Please Enter User Name");
        } else if (userPass == "" || userPass == null) {
            alert("Please Enter Password");
        } else {
            try {
                const response = await fetch('http://localhost:5000/auth/login',
                {
                  method: 'POST',
                  headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({
                    "username": userName,
                    "password": userPass
                  })
                });
                const token = await response.json();
                if (response.status == 200) {
                    document.getElementById('loginDiv').style.display = 'none';
                    window.localStorage.setItem('AUTH_TOKEN', token.token);
                    window.localStorage.setItem('USER', userName);
                    window.localStorage.removeItem('ROLE');
                    window.localStorage.setItem('ROLE', 'feed');
                    removePosts();
                    page = 0;
                    getHomePage();
                    getUser();
                } else {
                    alert('non-valid username/password');
                }
            } catch (e) {
                console.log('Err',e);
            }
        }
}); 

document.getElementById('followBtn').addEventListener('click', function() {follow('')}); 
async function follow(login_user = '') {
    var userName = document.getElementById('follow').value;
    if (login_user !== '') {
        userName = login_user;
    }
    const token = window.localStorage.getItem('AUTH_TOKEN');
    if (userName == "" || userName == null) {
        alert("Please Enter User Name");
    } else {
        try {
            const response = await fetch('http://localhost:5000/user?username=' + userName,
            {
              method: 'GET',
              headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                Authorization: `token ${token}`
              }
            });
            if (response.status == 200) {
                const response = await fetch('http://localhost:5000/user/follow?username=' + userName,
                {
                method: 'PUT',
                headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json',
                    Authorization: `token ${token}`
                }
                });
                if (response.status == 200) {
                    removePosts();
                    page = 0;
                    getHomePage();
                    console.log('follow sucess!');
                    document.getElementById('followDiv').style.display = 'none';
                } else {
                    alert('follow failed');
                }
            } else {
                alert('cannot find user ' + userName);
            }
        } catch (e) {
            console.log('Err',e);
        }
    }
}

async function getHomePage(userPage = '', start = 0) {
    page++;
    const token = window.localStorage.getItem('AUTH_TOKEN');
    try {
        const response = await fetch('http://127.0.0.1:5000/user/feed?p=' + start * 5 + '&n=' + (start + 1) * 5,
        {
          method: 'GET',
          headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            Authorization: `token ${token}`
          }
        });
        const data = await response.json();
        if (response.status == 200) {
            var array;
            if (userPage !== '') {
                array = data.posts.filter(e => e.meta.author === userPage);
            } else {
                array = data.posts;
            }
            array.reduce((parent, post) => {
                parent.appendChild(createPostTile(post, 'post'));
                addUserPageEvent(post);
                addLikeEvent(post);
                addCommentEvent(parent, post);
                addUnfollowEvent(post);
                addLikeModal(parent, post);
                addCommentModal(parent, post);
                return parent;
            }, document.getElementById('large-feed'))
        }
    } catch (e) {
        console.log('Err',e);
    }
}

var feed = document.querySelector('body');
feed.addEventListener('scroll', function() {
    var mode = localStorage.getItem('ROLE');
    if (feed.scrollTop + feed.clientHeight >= feed.scrollHeight) {
        if (mode === 'feed') {
            getHomePage('', page);
        } else {
            console.log('user', localStorage.getItem('USER'));
            getHomePage(localStorage.getItem('USER'), page);
        }
    }
});