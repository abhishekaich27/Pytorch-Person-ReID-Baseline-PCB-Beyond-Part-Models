import torch
from tools import time_now, CatMeter, ReIDEvaluator, fliplr


def test(config, base, loaders):

	def compute_feature(images):
		images_f = fliplr(images)
		images = images.to(base.device)
		images_f = images_f.to(base.device)
		features = base.model(images)
		features_f = base.model(images_f)
		features = features + features_f
		return features

	base.set_eval()

	# meters
	query_features_meter, query_pids_meter, query_cids_meter = CatMeter(), CatMeter(), CatMeter()
	gallery_features_meter, gallery_pids_meter, gallery_cids_meter = CatMeter(), CatMeter(), CatMeter()

	# init dataset
	if config.test_dataset == 'market':
		loaders = [loaders.market_query_loader, loaders.market_gallery_loader]
	elif config.test_dataset == 'duke':
		loaders = [loaders.duke_query_loader, loaders.duke_gallery_loader]

	# compute query and gallery features
	with torch.no_grad():
		for loader_id, loader in enumerate(loaders):
			for data in loader:
				# compute feautres
				images, pids, cids = data
				features = compute_feature(images)
				# save as query features
				if loader_id == 0:
					query_features_meter.update(features.data)
					query_pids_meter.update(pids)
					query_cids_meter.update(cids)
				# save as gallery features
				elif loader_id == 1:
					gallery_features_meter.update(features.data)
					gallery_pids_meter.update(pids)
					gallery_cids_meter.update(cids)

	#
	query_features = query_features_meter.get_val_numpy()
	gallery_features = gallery_features_meter.get_val_numpy()

	# compute mAP and rank@k
	mAP, CMC = ReIDEvaluator(dist='euclidean', mode=config.test_mode).evaluate(
		query_features, query_cids_meter.get_val_numpy(), query_pids_meter.get_val_numpy(),
		gallery_features, gallery_cids_meter.get_val_numpy(), gallery_pids_meter.get_val_numpy())

	return mAP, CMC[0: 150]


