(function(){

	// Models
	window.Account = Backbone.Model.extend({
		idAttribute: "id"
	});

	window.AccountCollection = Backbone.Collection.extend({
	    model:Account,
	    url:"/api/v1/account_lead"
	});

	window.MailingLists = Backbone.Model.extend({
		idAttribute: "id"
	});

	window.MailingListsCollection = Backbone.Collection.extend({
	    model:MailingLists,
	    url:"/api/v1/mailing_lists"
	});

	// Views
	window.AccountListView = Backbone.View.extend({

	    tagName:'ul',

	    initialize:function () {
	        this.model.bind("reset", this.render, this);
	    },

	    render:function (eventName) {
	        _.each(this.model.models, function (account) {
	            $(this.el).append(new AccountListItemView({model:account}).render().el);
	        }, this);
	        return this;
	    }

	});

	window.MailingListsListView = Backbone.View.extend({

	    tagName:'ul',

	    initialize:function () {
	        this.model.bind("reset", this.render, this);
	    },

	    render:function (eventName) {
	        _.each(this.model.models, function (mailingLists) {
	            $(this.el).append(new MailingListsItemView({model:mailingLists}).render().el);
	        }, this);
	        return this;
	    }

	});

	window.AccountListItemView = Backbone.View.extend({

	    tagName:"li",

	    template:_.template($('#tpl-account-list-item').html()),

	    render:function (eventName) {
	        $(this.el).html(this.template(this.model.toJSON()));
	        return this;
	    }

	});

	window.MailingListsItemView = Backbone.View.extend({

	    tagName:"li",

	    template:_.template($('#tpl-mailingLists-list-item').html()),

	    render:function (eventName) {
	        $(this.el).html(this.template(this.model.toJSON()));
	        return this;
	    }

	});

	window.AccountView = Backbone.View.extend({

	    template:_.template($('#tpl-account-details').html()),

	    render:function (eventName) {
	        $(this.el).html(this.template(this.model.toJSON()));
	        return this;
	    }

	});

	window.MailinglistsView = Backbone.View.extend({

	    template:_.template($('#tpl-mailingLists-details').html()),

	    render:function (eventName) {
	        $(this.el).html(this.template(this.model.toJSON()));
	        return this;
	    }

	});

	// Router
	var AppRouter = Backbone.Router.extend({

	    routes:{
	        "":"list",
	        "accounts/:id":"accountDetails",
	        "mailinglists/:id":"mailinglistsDetails"
	    },

	    list:function () {
	        this.accountList = new AccountCollection();
	        this.accountListView = new AccountListView({model:this.accountList});
	        this.accountList.fetch();
	        $('#list-accounts').html(this.accountListView.render().el);

	        this.mailingListsList = new MailingListsCollection();
	        this.mailingListsListView = new MailingListsListView({model:this.mailingListsList});
	        this.mailingListsList.fetch();
	        $('#list-mailing-lists').html(this.mailingListsListView.render().el);
	    },

	    accountDetails:function (id) {
	        this.account = this.accountList.get(id);
	        this.accountView = new AccountView({model:this.account});
	        $('#content').html(this.accountView.render().el);
	    },

	    mailinglistsDetails:function (id) {
	        this.mailinglists = this.mailingListsList.get(id);
	        this.mailinglistsView = new MailinglistsView({model:this.mailinglists});
	        $('#content').html(this.mailinglistsView.render().el);
	    }
	});

	var app = new AppRouter();
	Backbone.history.start();
})();