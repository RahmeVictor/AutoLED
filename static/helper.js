function post_data(location, data) {
    //serialize JSON body data
    data = JSON.stringify(data);
    fetch(location, {
        method: "post",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: data
    }).then(() => {
    });
}