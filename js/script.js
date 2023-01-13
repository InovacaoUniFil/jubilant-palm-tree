function geturl(incommingID){
    const token = "c94e0188-31fa-445b-b58b-cccb6d6efacd";
    let url = "https://unifilteste.movidesk.com/public/v1/persons?token=c94e0188-31fa-445b-b58b-cccb6d6efacd&id="+incommingID;

    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", url); // false for synchronous request 
    xmlHttp.responseType = "json";
    xmlHttp.send();

    return xmlHttp.response;
}