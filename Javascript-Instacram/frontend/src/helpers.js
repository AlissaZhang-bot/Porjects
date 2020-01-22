/* returns an empty array of size max */
export const range = (max) => Array(max).fill(null);

/* returns a randomInteger */
export const randomInteger = (max = 1) => Math.floor(Math.random()*max);

/* returns a randomHexString */
const randomHex = () => randomInteger(256).toString(16);

/* returns a randomColor */
export const randomColor = () => '#'+range(3).map(randomHex).join('');

/**
 * You don't have to use this but it may or may not simplify element creation
 * 
 * @param {string}  tag     The HTML element desired
 * @param {any}     data    Any textContent, data associated with the element
 * @param {object}  options Any further HTML attributes specified
 */
export function createElement(tag, data, options = {}) {
    const el = document.createElement(tag);
    el.textContent = data;
   
    // Sets the attributes in the options object to the element
    return Object.entries(options).reduce(
        (element, [field, value]) => {
            element.setAttribute(field, value);
            return element;
        }, el);
}

/**
 * Given a post, return a tile with the relevant data
 * @param   {object}        post 
 * @returns {HTMLElement}
 */
export function createPostTile(post, flag) {
    const section = createElement('section', null, { class: 'post' });
    section.appendChild(createElement('h2', post.meta.author, { class: 'post-title', id: 'h2_' + post.id }));
    var date = new Date(post.meta.published*1000);
    section.appendChild(createElement('p', date.toISOString().slice(0,10) + ' ' + date.toTimeString().split(' ')[0], { class: 'post-time' }));
    if (flag === 'mypage') {
        section.appendChild(createElement('span', 'Edit', { class: 'post-update', id: 'update_' + post.id }));
        section.appendChild(createElement('span', 'Delete', { class: 'post-delete', id: 'delete_' + post.id }));
        if (flag !== 'local') {
            var dataURL = 'data:image/png;base64,' + post.src;
            const image = createElement('img', null, { class: 'post-img', src: dataURL, id: 'img_' + post.id });
            section.appendChild(image);
        } else {
            section.appendChild(createElement('img', null, { class: 'post-img', src: '/images/'+post.src, alt: post.meta.description_text, class: 'post-image' }));
        }
    } else {
    if (flag !== 'local') {
        var dataURL = 'data:image/png;base64,' + post.src;
        const image = createElement('img', null, { class: 'post-img', src: dataURL, id: 'img_' + post.id });
        section.appendChild(image);
    } else {
        section.appendChild(createElement('img', null, { class: 'post-img', src: '/images/'+post.src, alt: post.meta.description_text, class: 'post-image' }));
    }
    var user_id = localStorage.getItem('USERID');

    var pEl = document.createElement('p');
    pEl.className = 'f_c_l_pEl';
    pEl.appendChild(createElement('b', ' unfollow ', { class: 'post-unfollow', id: 'f_' + post.id }));
    var is_liked = 0;
    for (var i = 0; i < post.meta.likes.length; i++) {
        if (post.meta.likes[i] == user_id) {
            is_liked = 1;
            break;
        }
    }
    if (is_liked == 1) {
        pEl.appendChild(createElement('b', ' unlike ', { class: 'post-like', id: 'l_' + post.id }));
    } else {
        pEl.appendChild(createElement('b', ' like ', { class: 'post-like', id: 'l_' + post.id }));
    }
    pEl.appendChild(createElement('b', ' comment ', { class: 'post-comment', id: 'c_' + post.id }));
    section.appendChild(pEl);
    }
    section.appendChild(createElement('p', post.meta.likes.length + ' likes ', { class: 'post-likes', id: 'like_' + post.id }));
    section.appendChild(createElement('p', post.comments.length + ' comments ', { class: 'post-comments', id: 'comment_' + post.id }));
    section.appendChild(createElement('p', post.meta.author + ' : ' + post.meta.description_text, { class: 'post-description' }));
    return section;
}

export function createLocalPostTile(post) {
    const section = createElement('section', null, { class: 'post' });
    section.appendChild(createElement('h2', post.meta.author, { class: 'post-title' }));
    section.appendChild(createElement('p', post.meta.published.slice(0,25), { class: 'post-time' }));
    section.appendChild(createElement('img', null, { class: 'post-img', src: '/images/'+post.src, alt: post.meta.description_text, class: 'post-image' }));
    section.appendChild(createElement('p', post.meta.author + ' : ' + post.meta.description_text, { class: 'post-description' }));
    return section;
}

// Given an input element of type=file, grab the data uploaded for use
//export 

/* 
    Reminder about localStorage
    window.localStorage.setItem('AUTH_KEY', someKey);
    window.localStorage.getItem('AUTH_KEY');
    localStorage.clear()
*/
export function checkStore(key) {
    if (window.localStorage)
        return window.localStorage.getItem(key)
    else
        return null

}