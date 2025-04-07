document.addEventListener('alpine:init', () => {
    Alpine.store('archiveRefs', {
        curr: []
    })
})

function addRefItem(templateRefItemId, refItemId) {
    let id = '#' + templateRefItemId
    let refList = document.querySelector("#references-list")
    let templateCopy = document.querySelector(id).content.cloneNode(true)
    refList.appendChild(templateCopy)
    Alpine.store("archiveRefs").curr.push(refItemId)
}
