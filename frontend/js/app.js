    Alpine.store('NotifToast', {
        color : "#007aff",
        appear : false,
        type : "",
        message : "",
        title : "",
        tm : null, // timeout        

 
        init(){
            console.log("NotifToast mounted");
            if( window.localStorage.getItem("notifType") != null ){
                let type = window.localStorage.getItem("notifType");
                let msg  = window.localStorage.getItem("notifMessage");
                window.localStorage.removeItem("notifType");
                window.localStorage.removeItem("notifMessage");
                
                switch(type){
                    case 'success' :                         
                        this.success(msg).show();
                        break;
                    case 'warning' : 
                        this.warning(msg).show();
                        break;
                    case 'error' : 
                        this.error(msg).show();
                        break;
                }
            }
            
        },

        getColor(){
            let color = "";

            switch(this.type){
                case "success" : color = "#198754"; break;
                case "warning" : color = "#975326"; break;
                case "error" : color = "#FF0000"; break;
            }
        
            return color;
        },

        error(message){
            this.title  = "Erreur";
            this.type  = "toast-error";
            this.message  = message;
            return this;  
        },

        success(message){
            this.title  = "";
            this.type  = "toast-success";
            this.message  = message;
            return this;  
        },
        
        info(message){
            this.title  = "Information";
            this.type  = "toast-info";
            this.message  = message;
            return this;  
        },

        warning(message){
            this.title  = "Attention !";
            this.type  = "toast-warning";
            this.message  = message;
            return this;  
        },

        show(){
            // TODO : copier element dans body
            // TODO : ajouter les un sous les autres si actif ( table )
            var x = document.getElementById("toast");
            
            
            // Add the "show" class to DIV
            x.classList.add(this.type);
            x.classList.add("show");
            
            
            // After 3 seconds, remove the show class from DIV
            this.tm = setTimeout(function(){ 
                x.classList.remove("show"); 
                x.removeAttribute('class')
            }, 5500);

            // this.appear = true;

            // if(this.tm != null) 
            //     clearTimeout(this.tm);  

            // this.tm = setTimeout(() => {this.appear = false},8000);  
        },

        close(){
            var x = document.getElementById("toast");
            x.classList.remove("show"); 
            x.removeAttribute('class')

            if(this.tm != null) 
                clearTimeout(this.tm);  

            this.appear = false;
        },        

        redirect(url){
            window.localStorage.setItem("notifType", this.type);            
            window.localStorage.setItem("notifMessage", this.message);                                
            window.location.href = url;
        },

        replace(url){
            window.localStorage.setItem("notifType", this.type);            
            window.localStorage.setItem("notifMessage", this.message);                                
            window.location.replace(url);
        },

    });